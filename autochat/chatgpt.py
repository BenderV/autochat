import json
import os
import typing

import openai
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from autochat.utils import csv_dumps, parse_function

# https://platform.openai.com/docs/models/gpt-4
DEFAULT_MODEL = "gpt-4"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


client = OpenAI()


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
            res["function_call"] = {
                "name": self.function_call["name"],
                "arguments": json.dumps(self.function_call["arguments"]),
            }
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


def split_message(message):
    """Split message into content and function_call_str
    > message = "boat > flight\n> attack()"
    > split_message(message)
    > ('boat > flight', 'attack()')
    """
    lines = message.split("\n")
    content = []
    function_call_str = []

    switch = False
    for line in lines:
        if line.startswith(">"):
            switch = True
            function_call_str.append(line[1:].strip())  # Remove the leading ">"
        else:
            if switch:
                function_call_str.append(line)
            else:
                content.append(line)

    return "\n".join(content), "\n".join(function_call_str)


def parse_chat_template(filename):
    with open(filename) as f:
        string = f.read()

    # split the string by "\n## " to get a list of speaker and message pairs
    pairs = string.split("## ")[1:]

    # split each element of the resulting list by "\n" to separate the speaker and message
    pairs = [pair.split("\n", 1) for pair in pairs]

    # create a list of tuples
    messages = [(pair[0], pair[1].strip()) for pair in pairs]

    examples = []
    instruction = None
    for ind, message in enumerate(messages):
        # If first message role is a system message, extract the example
        if ind == 0 and message[0] == "system":
            instruction = message[1]
        else:
            role = message[0].strip().lower()
            message = message[1]

            content, function_call_str = split_message(message)
            if function_call_str:
                examples.append(
                    {
                        "role": role,
                        "content": content if content else None,
                        "function_call": {**parse_function(function_call_str)},
                    }
                )
            else:
                examples.append(
                    {
                        "role": role,
                        "content": message,
                    }
                )
    return instruction, examples


class ChatGPT:
    def __init__(
        self,
        instruction=None,
        examples=[],
        context=None,
        max_interactions: int = 100,
    ) -> None:
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

        response = self.fetch_openai()
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
        ),
        # After 5 attempts, we throw the error
        reraise=True,
    )
    def fetch_openai(self):
        first_message = self.history[0].to_openai_dict()
        if self.context:
            first_message["content"] = self.context + "\n" + first_message["content"]
        messages: list[dict] = (
            [x.to_openai_dict() for x in self.pre_history]
            + [first_message]
            + [x.to_openai_dict() for x in self.history[1:]]
        )

        try:
            if self.functions_schema:
                res = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    functions=self.functions_schema,
                )
            else:
                res = client.chat.completions.create(
                    model=OPENAI_MODEL, messages=messages
                )
        except openai.BadRequestError as e:
            if e.code == "context_length_exceeded":
                raise ContextLengthExceededError(e)
            if e.code == "invalid_request_error":
                raise InvalidRequestError(e)
        except openai.APIError as e:
            raise e

        message = res.choices[0].message
        return Message.from_openai_dict(
            role=message.role,
            content=message.content,
            function_call=message.function_call,
            id=res.id,  # We use the response id as the message id
        )
