"""AutoChat package."""

__version__ = "0.4.1"

import json
import os
import traceback
import typing
import inspect
from enum import Enum

from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from autochat.model import Message, MessagePart
from autochat.utils import csv_dumps, inspect_schema, parse_chat_template
from PIL import Image as PILImage
import io

AUTOCHAT_HOST = os.getenv("AUTOCHAT_HOST")
AUTOCHAT_MODEL = os.getenv("AUTOCHAT_MODEL")
OUTPUT_SIZE_LIMIT = int(os.getenv("AUTOCHAT_OUTPUT_SIZE_LIMIT", 4000))


class APIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ContextLengthExceededError(Exception):
    pass


class InvalidRequestError(Exception):
    pass


class StopLoopException(Exception):
    pass


class InsufficientQuotaError(Exception):
    pass


class Autochat:
    def __init__(
        self,
        instruction: str = None,
        examples: list[Message] | None = None,
        messages: list[Message] | None = None,
        context: str = None,
        max_interactions: int = 100,
        model=AUTOCHAT_MODEL,
        provider=APIProvider.OPENAI,
    ) -> None:
        if isinstance(provider, APIProvider):
            self.provider = provider
        elif isinstance(provider, str):
            try:
                self.provider = APIProvider(provider)
            except ValueError:
                raise ValueError(f"Provider {provider} is not a valid provider")
        else:
            raise ValueError(f"Invalid provider: {provider}")

        self.model = model
        self.client = None
        self.instruction = instruction
        if examples is None:
            self.examples = []
        else:
            self.examples = examples

        if messages is None:
            self.messages = []
        else:
            self.messages = messages

        self.context = context
        self.max_interactions = max_interactions
        self.functions_schema = []
        self.functions = {}
        self.tools = {}
        # Give the hability to pause the conversation after a function call or response
        self.should_pause_conversation = lambda function_call, function_response: False

        if self.provider == APIProvider.OPENAI:
            from openai import OpenAI

            if self.model is None:
                # Default to gpt-4o
                self.model = "gpt-4o"
            self.client = OpenAI(
                base_url=(
                    f"{AUTOCHAT_HOST}/v1"
                    if AUTOCHAT_HOST
                    else "https://api.openai.com/v1"
                ),
                # We override because we have our own retry logic
                max_retries=0,  # default is 2
            )
            self.fetch = self.fetch_openai
        elif self.provider == APIProvider.ANTHROPIC:
            import anthropic

            if self.model is None:
                self.model = "claude-3-5-sonnet-20240620"
            self.client = anthropic.Anthropic(
                default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
            )
            self.fetch = self.fetch_anthropic
        else:
            raise ValueError(f"Invalid provider: {self.provider}")

    @classmethod
    def from_template(cls, chat_template: str, **kwargs):
        instruction, examples = parse_chat_template(chat_template)
        return cls(
            instruction=instruction,
            examples=examples,
            **kwargs,
        )

    def reset(self):
        """Reset the chat state.

        This will clear the chat history and reset the functions and tools.
        """
        self.messages = []
        self.functions_schema = []
        self.functions = {}
        self.tools = {}

    @property
    def last_message(self):
        if not self.messages:
            return None
        return self.messages[-1].content

    def load_messages(self, messages: list[Message]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        # messages = sorted(messages, key=lambda x: x.createdAt)
        self.messages = messages  # [message for message in messages]

    def add_function(
        self,
        function: typing.Callable,
        function_schema: typing.Optional[dict] = None,
    ):
        if function_schema is None:
            # We try to infer the function schema from the function
            function_schema = inspect_schema(function)

        self.functions_schema.append(function_schema)
        self.functions[function_schema["name"]] = function

    def add_tool(self, tool: typing.Union[type, object], tool_id: str = None) -> str:
        """Add a tool class or instance to the chat instance and return the tool id"""
        if isinstance(tool, type):
            # If a class is provided, instantiate it
            tool_instance = tool()
            tool_class = tool
        else:
            # If an instance is provided, use it directly
            tool_instance = tool
            tool_class = tool.__class__

        if not tool_id:
            tool_id = (
                "tool-" + str(id(tool_instance))
                if isinstance(tool, object)
                else tool_class.__name__
            )

        self.tools[tool_id] = tool_instance
        # Add all methods from the tool class to the functions schema
        for method_name, method in tool_class.__dict__.items():
            if not method_name.startswith("_"):  # Skip private methods
                if isinstance(method, classmethod):
                    method = method.__get__(None, tool_class)
                schema = inspect_schema(method)
                schema["name"] = f"{tool_id}__{method_name}"  # Prefix with class name
                self.functions_schema.append(schema)
                self.functions[schema["name"]] = getattr(tool_instance, method_name)
        return tool_id

    def remove_tool(self, tool_id: str):
        del self.tools[tool_id]
        self.functions_schema = [
            schema for schema in self.functions_schema if schema["name"] != tool_id
        ]
        self.functions = {
            name: func for name, func in self.functions.items() if name != tool_id
        }

    def prepare_messages(
        self,
        transform_function: typing.Callable,
        transform_list_function: typing.Callable = lambda x: x,
    ) -> list[dict]:
        """Prepare messages for API requests using a transformation function."""
        first_message = self.messages[0]
        if self.context:
            # Add context to the first message
            if isinstance(first_message.content, str):
                first_message.parts[0].content = (
                    self.context + "\n" + first_message.parts[0].content
                )
            elif isinstance(first_message.content, list):
                first_message.content = [
                    MessagePart(type="text", content=self.context),
                    *first_message.content,
                ]
        messages = self.examples + [first_message] + self.messages[1:]
        transform_list_function(messages)
        return [transform_function(m) for m in messages]

    def ask(
        self,
        message: typing.Union[Message, str, None] = None,
        **kwargs,
    ) -> Message:
        if message:
            if isinstance(message, str):
                # If message is instance of string, then convert to Message
                message = Message(
                    role="user",
                    content=message,
                )
            self.messages.append(message)  # Add the question to the history

        response = self.fetch(**kwargs)
        self.messages.append(response)
        return response

    def run_conversation(
        self,
        question: typing.Union[str, Message, None] = None,
    ) -> typing.Generator[Message, None, None]:
        # If there's an initial question, emit it:
        if isinstance(question, str):
            message = Message(
                role="user",
                content=question,
            )
            yield message
        else:
            message = question

        for _ in range(self.max_interactions):
            # TODO: Check if the user has stopped the conversation

            # Ask the LLM with the current message (if any)
            response = self.ask(message)

            # TODO: Add support for multiple function calls
            # Locate a function_call part in the assistant's response
            function_call_part = next(
                (p for p in response.parts if p.type == "function_call"), None
            )
            if not function_call_part:
                # If there's no function call part, it's presumably the final answer
                yield response
                return

            # Extract name and arguments from the function_call part
            function_name = function_call_part.function_call["name"]
            function_arguments = function_call_part.function_call["arguments"]

            image = None
            content = None

            # Attempt to call the function/tool
            def call_with_args(func, **kwargs):
                sig = inspect.signature(func)
                # Only include from_response if it's in the function's parameters
                if "from_response" in sig.parameters:
                    kwargs["from_response"] = response
                return func(**kwargs)

            try:
                if function_name.startswith("tool-"):
                    tool_id, method_name = function_name.split("__")
                    tool = self.tools[tool_id]
                    method = tool.__getattribute__(method_name)
                    content = call_with_args(method, **function_arguments)
                else:
                    content = call_with_args(
                        self.functions[function_name], **function_arguments
                    )
            except Exception as e:
                if isinstance(e, StopLoopException):
                    yield response
                    return

                # We clean the traceback to remove frames from __init__.py
                tb = traceback.extract_tb(e.__traceback__)
                filtered_tb = [
                    frame for frame in tb if "__init__.py" not in frame.filename
                ]
                if filtered_tb:
                    content = "Traceback (most recent call last):\n"
                    content += "".join(traceback.format_list(filtered_tb))
                    content += f"\n{e.__class__.__name__}: {str(e)}"
                else:
                    # If no relevant frames, use the full traceback
                    content = traceback.format_exc()

            # Yield the assistant message that contained the function call
            yield response

            # We format the function_call response to be used as a next message
            if not isinstance(content, Message):
                if content is None:
                    # If no result, continue the loop with no additional message
                    content = None
                elif isinstance(content, list):
                    # If data is list of dicts, dumps to CSV
                    if not content:
                        content = "[]"
                    elif isinstance(content[0], dict):
                        content = csv_dumps(content, OUTPUT_SIZE_LIMIT)
                    else:  # TODO: Add support for other types of list
                        content = "\n".join(content)
                elif isinstance(content, dict):
                    content = json.dumps(content)
                    if len(content) > OUTPUT_SIZE_LIMIT:
                        content = (
                            content[:OUTPUT_SIZE_LIMIT]
                            + f"\n... ({len(content)} characters)"
                        )
                elif isinstance(content, str):
                    if len(content) > OUTPUT_SIZE_LIMIT:
                        content = (
                            content[:OUTPUT_SIZE_LIMIT]
                            + f"\n... ({len(content)} characters)"
                        )
                elif isinstance(content, bytes):
                    # Detect if it's an image
                    try:
                        image = PILImage.open(io.BytesIO(content))
                        content = None
                    except IOError:
                        # Not an image
                        raise ValueError("Returned bytes is not a valid image.")
                elif isinstance(content, (int, float, bool)):
                    content = str(content)
                elif isinstance(content, object):
                    # If the function return an object, we add it as a tool
                    # NOTE: Maybe we shouldn't, and rely on a clearer signal / object type ?
                    tool_id = self.add_tool(content)
                    content = f"Added tool: {tool_id}"
                else:
                    raise ValueError(f"Invalid content type: {type(content)}")

                # Build a function response message
                message = Message(
                    name=function_name,
                    role="function",
                    content=content,
                    image=image,
                    function_call_id=function_call_part.function_call_id,
                )
            else:
                # If the function returned a new Message, that becomes the next message
                message = content

            yield message

            # If user code wants to pause:
            if self.should_pause_conversation(response, message):
                return

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=2, max=10),
        # If we get a context_length_exceeded error, we stop the conversation
        retry=(
            retry_if_not_exception_type(ContextLengthExceededError)
            & retry_if_not_exception_type(InvalidRequestError)
            & retry_if_not_exception_type(InsufficientQuotaError)
            & retry_if_not_exception_type(
                AttributeError
            )  # TODO: should only retry if the error is from the api
        ),
        # After 5 attempts, we throw the error
        reraise=True,
    )
    def fetch_openai(self, **kwargs):
        import openai

        messages = self.prepare_messages(transform_function=Message.to_openai_dict)
        # Add instruction as the first message
        if self.instruction:
            instruction_message = Message(
                role="system",
                content=self.instruction,
            )
            messages = [instruction_message.to_openai_dict()] + messages

        try:
            if self.functions_schema:
                res = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=self.functions_schema,
                    **kwargs,
                )
            else:
                res = self.client.chat.completions.create(
                    model=self.model, messages=messages, **kwargs
                )
        except openai.BadRequestError as e:
            if e.code == "context_length_exceeded":
                raise ContextLengthExceededError(e)
            if e.code == "invalid_request_error":
                raise InvalidRequestError(e)
            raise
        except openai.RateLimitError as e:
            if e.code == "insufficient_quota":
                raise InsufficientQuotaError(e)
            raise
        except openai.APIError as e:
            raise e

        message = res.choices[0].message
        return Message.from_openai_dict(
            role=message.role,
            content=message.content,
            function_call=message.function_call,
            id=res.id,  # We use the response id as the message id
        )

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=2, max=10),
        # If we get a context_length_exceeded error, we stop the conversation
        retry=(
            retry_if_not_exception_type(ContextLengthExceededError)
            & retry_if_not_exception_type(InvalidRequestError)
            & retry_if_not_exception_type(InsufficientQuotaError)
            & retry_if_not_exception_type(
                TypeError
            )  # TODO: should only retry if the error is from the api
        ),
        # After 5 attempts, we throw the error
        reraise=True,
    )
    def fetch_anthropic(self, **kwargs):
        def add_empty_function_result(messages):
            """
            Ajustement Anthropic pour fusionner ou insérer la « function_result » :

            - Premier cas : message `role="function"` suivi d’un `role="user"`.
            On transforme ce message 'function' en un part de type 'tool_result'
            inséré au début du message utilisateur suivant.

            - Second cas (inchangé) : message `role="assistant"` avec un `function_call`,
            suivi d’un message non-`function`. On insère un message vide `role="function"`.
            """
            for i in range(len(messages) - 1, 0, -1):
                if (
                    messages[i - 1].role == "assistant"
                    and messages[i - 1].function_call
                    and not messages[i].role == "function"
                ):
                    # Insert an empty function result
                    messages.insert(
                        i,
                        Message(
                            role="function",
                            name=messages[i - 1].function_call["name"],
                            content="",
                            function_call_id=messages[i - 1].function_call_id,
                        ),
                    )

        messages = self.prepare_messages(
            transform_function=lambda m: m.to_anthropic_dict(),
            transform_list_function=add_empty_function_result,
        )

        if self.instruction:
            system = self.instruction
        else:
            system = None

        def merge_messages(messages):
            """
            When two messages are in the same role, we merge the following message into the previous.
            {
                "role": "user",
                "content": [
                    {
                    "type": "tool_result",
                    "tool_use_id": "example_19",
                    "content": ""
                    }
                ]
            },
            {
                "role": "user",
                "content": "Plot distribution of stations per city"
            }
            """
            merged_messages = []
            for message in messages:
                if merged_messages and merged_messages[-1]["role"] == message["role"]:
                    if isinstance(merged_messages[-1]["content"], str):
                        merged_messages[-1]["content"].append(
                            {
                                "type": "text",
                                "text": merged_messages[-1]["content"],
                            }
                        )
                    elif isinstance(merged_messages[-1]["content"], list):
                        merged_messages[-1]["content"].extend(message["content"])
                    else:
                        raise ValueError(
                            f"Invalid content type: {type(merged_messages[-1]['content'])}"
                        )
                else:
                    merged_messages.append(message)
            return merged_messages

        messages = merge_messages(messages)

        # Need to map field "parameters" to "input_schema"
        tools = [
            {
                "name": s["name"],
                "description": s["description"],
                "input_schema": s["parameters"],
            }
            for s in self.functions_schema
        ]
        # Add description to the function is their description is empty
        for tool in tools:
            if not tool["description"]:
                tool["description"] = "No description provided"

        # === Add cache_controls ===
        # Messages: Find the last message with an index multiple of 10
        last_message_index = next(
            (i for i in reversed(range(len(messages))) if i % 10 == 0),
            None,
        )

        if last_message_index is not None:
            if isinstance(messages[last_message_index]["content"], list) and isinstance(
                messages[last_message_index]["content"][-1], dict
            ):
                messages[last_message_index]["content"][-1]["cache_control"] = {
                    "type": "ephemeral"
                }
            elif isinstance(messages[last_message_index]["content"], str):
                messages[last_message_index]["content"] = [
                    {
                        "type": "text",
                        "text": messages[last_message_index]["content"],
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
        # Tools: Add cache_control to the last tool function
        if tools:
            tools[-1]["cache_control"] = {"type": "ephemeral"}

        # System: add cache_control to the system message
        if system is not None:
            system = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]

        # === End of cache_control ===

        if system is not None:
            kwargs["system"] = system

        res = self.client.messages.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=2000,
            **kwargs,
        )
        res_dict = res.to_dict()
        return Message.from_anthropic_dict(
            role=res_dict["role"],
            content=res_dict["content"],
        )
