import json
import os
import typing
from enum import Enum

from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .utils import csv_dumps, parse_chat_template

AUTOCHAT_HOST = os.getenv("AUTOCHAT_HOST")
AUTOCHAT_MODEL = os.getenv("AUTOCHAT_MODEL")


class APIProvider(Enum):
    OPENAI = "openai"


class FunctionCallParsingError(Exception):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return f"Invalid function_call: {self.obj.function_call}"


class ContextLengthExceededError(Exception):
    pass


class InvalidRequestError(Exception):
    pass


class StopLoopException(Exception):
    pass


class InsufficientQuotaError(Exception):
    pass


class Message:
    def __init__(
        self,
        role: str,
        content: str = None,
        name: typing.Optional[str] = None,
        function_call: typing.Optional[dict] = None,
        id: typing.Optional[int] = None,
    ) -> None:
        self.role = role
        self.content = content
        self.name = name
        self.function_call = function_call
        self.id = id

    def to_openai_dict(self) -> dict:
        res = {
            "role": self.role,
            "content": self.content,
        }
        if self.name:
            res["name"] = self.name
        if self.function_call:
            if self.role == "assistant":
                res["function_call"] = {
                    "name": self.function_call["name"],
                    "arguments": json.dumps(self.function_call["arguments"]),
                }
            else:
                # If user is triggering a function, we add the function call to the content
                # since openai doesn't support functions for user messages
                res["content"] = (
                    self.function_call["name"]
                    + ":"
                    + json.dumps(self.function_call["arguments"])
                )
        return res

    @classmethod
    def from_openai_dict(cls, **kwargs):
        obj = cls(**kwargs)
        if obj.function_call:
            # Parse function_call with json.loads
            try:
                obj.function_call = {
                    "name": obj.function_call.name,
                    "arguments": json.loads(obj.function_call.arguments),
                }
            except json.decoder.JSONDecodeError:
                raise FunctionCallParsingError(obj)
        return obj

    def __repr__(self) -> str:
        text = f"Message(role={self.role}, "
        if self.content:
            text += f'content="{self.content}", '
        if self.function_call:
            text += f'function_call="{self.function_call}", '
        return text[:-2] + ")"

    def to_markdown(self) -> str:
        text = f"## {self.role}\n"
        if self.content is not None:
            text += self.content + "\n"
        if self.function_call is not None:
            # Display function_call so it look like func(arg1="value1", arg2="value2")
            text += f"> {self.function_call['name']}({', '.join([f'{k}={v}' for k, v in self.function_call['arguments'].items()])})\n"
        if self.content is None and self.function_call is None:
            raise ValueError("Message should have content or function_call")
        return text


class ChatGPT:
    def __init__(
        self,
        instruction=None,
        examples=[],
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
        self.pre_history: list[Message] = []
        self.history: list[Message] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples
        self.context = context
        self.max_interactions = max_interactions
        self.functions_schema = []
        self.functions = {}

        if self.instruction:
            self.pre_history.append(Message(role="system", content=self.instruction))

        # Simple loop
        for example in self.examples:
            # Herit name from message role
            self.pre_history.append(
                Message(
                    **example,
                    name="example_" + example["role"],
                )
            )

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

    def add_function(self, function, function_schema):
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
                content = self.functions[function_name](
                    **function_arguments,
                    from_response=response,
                )
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
                message = None
                continue
            # If data is list of dicts, dumps to CSV
            if isinstance(content, list):
                if not content:
                    content = "[]"
                elif isinstance(content[0], dict):
                    try:
                        content = csv_dumps(content)
                    except Exception as e:
                        print(e)
                else:
                    content = "\n".join(content)
            message = Message(
                name=function_name,
                role="function",
                content=content,
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
