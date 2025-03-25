"""AutoChat package."""

__version__ = "0.4.1"

import inspect
import io
import json
import os
import traceback
import typing
import warnings

from PIL import Image as PILImage

from autochat.base import AutochatBase
from autochat.model import Message
from autochat.providers.base_provider import APIProvider
from autochat.providers.utils import get_provider_and_model
from autochat.utils import csv_dumps, inspect_schema, parse_chat_template

AUTOCHAT_HOST = os.getenv("AUTOCHAT_HOST")
AUTOCHAT_MODEL = os.getenv("AUTOCHAT_MODEL")
OUTPUT_SIZE_LIMIT = int(os.getenv("AUTOCHAT_OUTPUT_SIZE_LIMIT", 4000))


class StopLoopException(Exception):
    pass


def simple_response_default_callback(response: Message) -> Message:
    """
    This function is called when the response is a simple response (no function call).
    By default, the conversation will stop after a simple response.
    You can override this function to change this behavior.
    """
    raise StopLoopException("Stopping the conversation after a simple response")


class Autochat(AutochatBase):
    def __init__(
        self,
        instruction: str = None,
        examples: typing.Union[list[Message], None] = None,
        messages: typing.Union[list[Message], None] = None,
        context: str = None,
        max_interactions: int = 100,
        model=AUTOCHAT_MODEL,
        provider: str = APIProvider.OPENAI,
        use_tools_only: bool = False,
    ) -> None:
        """
        Initialize the Autochat instance.
        Args:
            use_tools_only: bool = False,
                If True, the chat will only use tools and not the LLM.
                This is a beta feature and may change in the future.
        """
        self.provider, self.model = get_provider_and_model(
            self, provider, model
        )  # TODO: rename register ?
        self.simple_response_callback = simple_response_default_callback
        if use_tools_only:
            warnings.warn(
                "use_tools_only is a beta feature and may change in the future"
            )
        self.use_tools_only = use_tools_only
        self.client = None  # TODO:
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

    @property
    def last_tools_states(self) -> typing.Optional[str]:
        """We add the repr() of each tool to the system context"""
        # If there are no tools, return None
        if not self.tools:
            return None
        tool_reprs = []
        for tool_id, tool in self.tools.items():
            tool_name = f"{tool.__class__.__name__}-{tool_id}"
            if hasattr(tool, "__repr__"):
                tool_reprs.append(f"### {tool_name}\n{repr(tool)}")

        tool_context = "\n".join(tool_reprs)

        """
        ## Last Tools States
        ### Tool 1
        {state}
        ### Tool 2
        {state}
        --- End of Last Tools States ---
        """
        return f"## Last Tools States\n{tool_context}\n--- End of Last Tools States ---"

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

    def add_tool(
        self, tool: typing.Union[type, object], tool_id: typing.Optional[str] = None
    ) -> str:
        """Add a tool class or instance to the chat instance and return the tool id"""
        if isinstance(tool, type):
            # If a class is provided, instantiate it
            tool = tool()

        if tool_id is None:
            tool_id = str(id(tool))

        self.tools[tool_id] = tool

        class_name = tool.__class__.__name__
        tool_name = f"{class_name}-{tool_id}"
        for method_name, method in inspect.getmembers(tool, inspect.ismethod):
            if method_name.startswith("_"):  # Skip private methods
                continue
            function_schema = inspect_schema(method)
            function_schema["name"] = f"{tool_name}__{method_name}"
            self.add_function(method, function_schema)
        return tool_id

    def remove_tool(self, tool_id: str):
        del self.tools[tool_id]
        self.functions_schema = [
            schema for schema in self.functions_schema if schema["name"] != tool_id
        ]
        self.functions = {
            name: func for name, func in self.functions.items() if name != tool_id
        }

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

        # 3. Call the strategy
        response = self.provider.fetch(**kwargs)
        self.messages.append(response)
        return response

    def _format_callback_message(
        self, function_name, function_call_part_id, content, image
    ):
        if isinstance(content, Message):
            message = content
            # TODO: Add name and function_call_id to the message
            # message.name = function_name
            # message.function_call_id = function_call_part_id
            return message

        # We format the function_call response to be used as a next message
        if content is None:
            # When content is None, use an empty string instead to prevent the "Message should have at least one part" error
            formatted_content = ""
        elif isinstance(content, list):
            formatted_content = []
            if not content:
                formatted_content = "[]"
            elif isinstance(content[0], dict):
                # If data is list of dicts, dumps to CSV
                formatted_content = csv_dumps(content, OUTPUT_SIZE_LIMIT)
            else:
                for item in content:
                    if isinstance(item, str):
                        formatted_content.append(item)
                    elif isinstance(item, object):
                        tool_id = self.add_tool(item)
                        formatted_content.append(f"Added tool: {tool_id}")
                    elif isinstance(item, (int, float, bool)):
                        formatted_content.append(str(item))
                    else:
                        raise ValueError(f"Invalid item type: {type(item)}")
            formatted_content = "\n".join(formatted_content)
            # Limit the size of the content
            if len(formatted_content) > OUTPUT_SIZE_LIMIT:
                formatted_content = (
                    formatted_content[:OUTPUT_SIZE_LIMIT]
                    + f"\n... ({len(formatted_content)} characters)"
                )
        elif isinstance(content, dict):
            content_dump = json.dumps(content)
            if len(content_dump) > OUTPUT_SIZE_LIMIT:
                formatted_content = (
                    content_dump[:OUTPUT_SIZE_LIMIT]
                    + f"\n... ({len(content_dump)} characters)"
                )
            else:
                formatted_content = content_dump
        elif isinstance(content, str):
            if len(content) > OUTPUT_SIZE_LIMIT:
                formatted_content = (
                    content[:OUTPUT_SIZE_LIMIT] + f"\n... ({len(content)} characters)"
                )
            else:
                formatted_content = content
        elif isinstance(content, bytes):
            # Detect if it's an image
            try:
                image = PILImage.open(io.BytesIO(content))
                formatted_content = None
            except IOError:
                # Not an image
                raise ValueError("Returned bytes is not a valid image.")
        elif isinstance(content, PILImage.Image):
            image = content
            formatted_content = None
        elif isinstance(content, (int, float, bool)):
            formatted_content = str(content)
        elif isinstance(content, object):
            # If the function return an object, we add it as a tool
            # NOTE: Maybe we shouldn't, and rely on a clearer signal / object type ?
            tool_id = self.add_tool(content)
            formatted_content = f"Added tool: {tool_id}"
        else:
            raise ValueError(f"Invalid content type: {type(content)}")

        # Build a function response message
        return Message(
            name=function_name,
            role="function",
            content=formatted_content,
            image=image,
            function_call_id=function_call_part_id,
        )

    def _format_exception(self, e):
        # We clean the traceback to remove frames from __init__.py
        tb = traceback.extract_tb(e.__traceback__)
        filtered_tb = [frame for frame in tb if "chat.py" not in frame.filename]
        if filtered_tb:
            content = "Traceback (most recent call last):\n"
            content += "".join(traceback.format_list(filtered_tb))
            content += f"\n{e.__class__.__name__}: {str(e)}"
        else:
            # If no relevant frames, use the full traceback
            content = traceback.format_exc()
        return content

    def _call_with_signature(self, func, from_response, **kwargs):
        sig = inspect.signature(func)
        if "from_response" in sig.parameters:
            return func(**kwargs, from_response=from_response)
        else:
            return func(**kwargs)

    def _call_function_and_build_message(
        self, function_name, function_arguments, response
    ):
        """
        Encapsulate the 'call the function' logic & handle exceptions
        plus building a function or tool response message.
        """
        content = None
        image = None

        try:
            if function_name.startswith("tool-"):
                tool_id, method_name = function_name.split("__")
                tool = self.tools[tool_id]
                method = getattr(tool, method_name)
                content = self._call_with_signature(
                    method, response, **function_arguments
                )
            else:
                content = self._call_with_signature(
                    self.functions[function_name], response, **function_arguments
                )
        except StopLoopException:
            raise
        except Exception as e:
            content = self._format_exception(e)

        # Build next message
        return self._format_callback_message(
            function_name=function_name,
            function_call_part_id=response.function_call_id,
            content=content,
            image=image,
        )

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
                yield response
                try:
                    message = self.simple_response_callback(response)
                except StopLoopException:
                    return
            else:
                name = function_call_part.function_call["name"]
                args = function_call_part.function_call["arguments"]

                try:
                    message = self._call_function_and_build_message(
                        name, args, response
                    )
                except StopLoopException:
                    return
                finally:
                    yield response  # Should be after call function so we can use the response object (from_response)
                yield message
