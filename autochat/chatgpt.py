import json
import os
import typing

import openai
from utils import parse_function

# https://platform.openai.com/docs/models/gpt-4
DEFAULT_MODEL = "gpt-4"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


class ConversationMessage:
    def __init__(
        self,
        role: str,
        content: str = None,
        name: typing.Optional[str] = None,
        function_call: typing.Optional[dict] = None,
        max_interactions: int = 100,
    ) -> None:
        self.role = role
        self.content = content
        self.name = name
        self.function_call = function_call
        self.max_interactions = max_interactions

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
            obj.function_call["arguments"] = json.loads(obj.function_call["arguments"])
        return obj

    def __repr__(self) -> str:
        if self.content:
            return f"{self.role}: {self.content}"
        elif self.function_call:
            # Display function_call so it look like func(arg1="value1", arg2="value2")
            return f"{self.role}: {self.function_call['name']}({', '.join([f'{k}={v}' for k, v in self.function_call['arguments'].items()])})"
        else:
            raise ValueError("Message should have content or function_call")


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

            if ">>>" in message:
                content, function_call_str = message.split(">>> ")
                examples.append(
                    {
                        "role": role,
                        "content": content,
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
    ) -> None:
        self.pre_history: list[ConversationMessage] = []
        self.history: list[ConversationMessage] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples
        self.context = context
        self.functions_schema = []
        self.functions = {}

        if self.instruction:
            self.pre_history.append(
                ConversationMessage(role="system", content=self.instruction)
            )

        # Simple loop
        for example in self.examples:
            # Herit name from message role
            self.pre_history.append(
                ConversationMessage(
                    **example,
                    name="example_" + example["role"],
                )
            )

    @classmethod
    def from_template(cls, chat_template: str):
        instruction, examples = parse_chat_template(chat_template)
        return cls(
            instruction=instruction,
            examples=examples,
        )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1].content

    def reset(self):
        self.history: list[ConversationMessage] = []

    def load_history(self, messages: list[ConversationMessage]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        messages = sorted(messages, key=lambda x: x.createdAt)
        self.history = [message for message in messages]

    def add_function(self, function, function_schema):
        self.functions_schema.append(function_schema)
        self.functions[function_schema["name"]] = function

    def ask(
        self,
        message: typing.Union[ConversationMessage, str, None] = None,
    ) -> ConversationMessage:
        if message:
            if isinstance(message, str):
                # If message is instance of string, then convert to ConversationMessage
                message = ConversationMessage(
                    role="user",
                    content=message,
                )
            self.history.append(message)  # Add the question to the history

        response = self.fetch_openai()
        self.history.append(response)
        return response

    def run_conversation(self, question: str):
        message = ConversationMessage(
            role="user",
            content=question,
        )

        for _ in range(self.max_interactions):
            # TODO: Check if the user has stopped the query

            response = self.ask(message)
            yield response

            if not response.function_call:
                return

            # Handle function calls
            function_name = response.function_call["name"]
            function_arguments = response.function_call["arguments"]
            content = self.functions[function_name](**function_arguments)
            message = ConversationMessage(
                name=function_name,
                role="function",
                content=content,
            )
            yield message

    def fetch_openai(self):
        first_message = self.history[0].to_openai_dict()
        if self.context:
            first_message["content"] = self.context + "\n" + first_message["content"]
        messages: list[dict] = (
            [x.to_openai_dict() for x in self.pre_history]
            + [first_message]
            + [x.to_openai_dict() for x in self.history[1:]]
        )
        res = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=messages,
            functions=self.functions_schema,
        )
        message = res.choices[0].message
        function_call = message.get("function_call")
        return ConversationMessage.from_openai_dict(
            role=message.role,
            content=message.content,
            function_call=function_call,
        )
