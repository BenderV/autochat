import json
import os
import typing
from enum import Enum

from tenacity import (retry, retry_if_not_exception_type, stop_after_attempt,
                      wait_random_exponential)

from .model import Message
from .utils import csv_dumps, inspect_schema, parse_chat_template

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


class ChatGPT:
    def __init__(
        self,
        messages: list[Message],
        context=None,
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
        self.messages: list[Message] = messages
        self.history: list[Message] = []
        self.context = context
        self.max_interactions = max_interactions
        self.functions_schema = []
        self.functions = {}

        # TODO: Remove this
        self.pre_history = messages
        self.history = []

        if self.provider == APIProvider.OPENAI:
            from openai import OpenAI

            if self.model is None:
                # Default to gpt-4-turbo
                self.model = "gpt-4-turbo"
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
        messages = parse_chat_template(chat_template)
        return cls(
            messages=messages,
            **kwargs,
        )

    @classmethod
    def from_instruction_and_examples(
        cls, instruction: str, examples: list[dict], **kwargs
    ):
        messages = [Message(role="system", content=instruction)] + [
            Message(**example) for example in examples
        ]
        return cls(
            messages=messages,
            **kwargs,
        )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1].content

    def reset_history(self):
        self.history: list[Message] = []

    def load_history(self, messages: list[Message]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        # messages = sorted(messages, key=lambda x: x.createdAt)
        self.history = messages  # [message for message in messages]

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

    def compress_history(self):
        """Try to make a summary of the history"""
        # TODO: Implement

    def prepare_messages(self, transform_function) -> list[dict]:
        """Prepare messages for API requests using a transformation function."""
        first_message = self.history[0]
        if self.context:
            first_message.content = self.context + "\n" + first_message.content
        messages = self.pre_history + [first_message] + self.history[1:]
        return [transform_function(m) for m in messages]

    def ask(
        self,
        message: typing.Union[Message, str, None] = None,
    ) -> Message:
        if message:
            if isinstance(message, str):
                # If message is instance of string, then convert to Message
                message = Message(
                    role="user",
                    content=message,
                )
            self.history.append(message)  # Add the question to the history

        response = self.fetch()
        self.history.append(response)
        return response

    def run_conversation(
        self, question: str = None
    ) -> typing.Generator[Message, None, None]:
        if question:
            message = Message(
                role="user",
                content=question,
            )
            yield message
        else:
            message = None

        for _ in range(self.max_interactions):
            # TODO: Check if the user has stopped the query
            response = self.ask(message)

            if not response.function_call:
                # We stop the conversation if the response is not a function call
                yield response
                return

            function_name = response.function_call["name"]
            function_arguments = response.function_call["arguments"]

            try:
                try:
                    content = self.functions[function_name](
                        **function_arguments,
                        from_response=response,
                    )
                except TypeError:
                    # If the function does not accept 'from_response', call it without that argument
                    content = self.functions[function_name](**function_arguments)
            except Exception as e:
                if isinstance(e, StopLoopException):
                    yield response
                    return
                # If function call failed, return the error message
                # Flatten the error message
                content = e.__repr__()

            yield response

            if content is None:
                # If function call returns None, we continue the conversation without adding a message
                # message = None
                # continue
                content = None
            elif isinstance(content, list):  # If data is list of dicts, dumps to CSV
                if not content:
                    content = "[]"
                elif isinstance(content[0], dict):
                    try:
                        content = csv_dumps(content, OUTPUT_SIZE_LIMIT)
                    except Exception as e:
                        print(e)
                else:
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
            else:
                raise ValueError(f"Invalid content type: {type(content)}")

            message = Message(
                name=function_name,
                role="function",
                content=content,
                function_call_id=response.function_call_id,
            )
            yield message

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=2, max=10),
        # If we get a context_length_exceeded error, we stop the conversation
        retry=(
            retry_if_not_exception_type(ContextLengthExceededError)
            & retry_if_not_exception_type(InvalidRequestError)
            & retry_if_not_exception_type(InsufficientQuotaError)
        ),
        # After 5 attempts, we throw the error
        reraise=True,
    )
    def fetch_openai(self):
        import openai

        messages = self.prepare_messages(transform_function=Message.to_openai_dict)

        try:
            if self.functions_schema:
                res = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=self.functions_schema,
                )
            else:
                res = self.client.chat.completions.create(
                    model=self.model, messages=messages
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
        ),
        # After 5 attempts, we throw the error
        reraise=True,
    )
    def fetch_anthropic(self):
        # Anthropic fix for empty function call result
        # Iterate on messages and check if the last message is a function call, and the following is a user text
        # If so, we have to add an empty result of the function call before the user text
        for i in range(len(self.history) - 1, 0, -1):
            if (
                self.history[i - 1].role == "assistant"
                and self.history[i - 1].function_call
                and self.history[i].role == "user"
                and not self.history[i].function_call
            ):
                print(f"Inserting empty function result: {i}")
                # Insert an empty function result
                self.history.insert(
                    i,
                    Message(
                        role="function",
                        name=self.history[i - 1].function_call["name"],
                        content="",
                        function_call_id=self.history[i - 1].function_call_id,
                    ),
                )

        messages = self.prepare_messages(
            transform_function=lambda m: m.to_anthropic_dict()
        )

        # Add cache control to the last message
        if (
            messages
            and isinstance(messages[-1]["content"], list)
            and len(messages[-1]["content"]) > 1
        ):
            messages[-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}

        system = messages[0]["content"]
        messages = messages[1:]

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
                    merged_messages[-1]["content"].append(
                        {
                            "type": "text",
                            "text": message["content"],
                        }
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

        res = self.client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=2000,
        )
        res_dict = res.to_dict()
        return Message.from_anthropic_dict(
            role=res_dict["role"],
            content=res_dict["content"],
        )
