import json
import typing
import base64
from io import BytesIO
from typing import Literal

from PIL import Image as PILImage


class FunctionCallParsingError(Exception):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return f"Invalid function_call: {self.obj.function_call}"


class Image:
    def __init__(self, image: PILImage.Image):
        self.image = image

    def resize(self, size: tuple[int, int]):
        self.image = self.image.resize(size)

    def to_base64(self):
        buffered = BytesIO()
        self.image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    @property
    def format(self):
        return "image/" + self.image.format.lower()


class Message:
    def __init__(
        self,
        role: Literal["user", "assistant", "function"],
        content: str = None,
        name: typing.Optional[str] = None,
        function_call: typing.Optional[dict] = None,
        id: typing.Optional[int] = None,
        function_call_id: typing.Optional[str] = None,
        image: typing.Optional[Image] = None,
    ) -> None:
        self.role = role
        self.content = content
        self.name = name
        self.function_call = function_call
        self.id = id
        self.function_call_id = function_call_id
        self.image = image

    def to_openai_dict(self) -> dict:
        res = {
            "role": self.role,
            "content": [],
        }
        if self.content:
            res["content"].append(
                {
                    "type": "text",
                    "text": self.content,
                }
            )
        if self.image:
            res["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{self.image.format};base64,{self.image.to_base64()}"
                    },
                }
            )
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
                # since openai doesn't support functions from user messages
                res["content"] = (
                    self.function_call["name"]
                    + ":"
                    + json.dumps(self.function_call["arguments"])
                )
        return res

    def to_anthropic_dict(self) -> dict:
        res = {
            "role": self.role if self.role in ["user", "assistant"] else "user",
            "content": [],
        }

        if self.role == "function":  # result of a function call
            res["content"] = [
                {
                    "type": "tool_result",
                    "tool_use_id": self.function_call_id,
                    "content": self.content,
                }
            ]
            return res

        if self.content:
            res["content"].append(
                {
                    "type": "text",
                    "text": self.content,
                }
            )
        if self.function_call:
            res["content"].append(
                {
                    "type": "tool_use",
                    "id": self.function_call_id,
                    "name": self.function_call["name"],
                    "input": self.function_call["arguments"],
                }
            )
        if self.image:
            res["content"].append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": self.image.format,
                        "data": self.image.to_base64(),
                    },
                }
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

    @classmethod
    def from_anthropic_dict(cls, **kwargs):
        role = kwargs.get("role")
        content = kwargs.get("content")

        if isinstance(content, str):
            return cls(role=role, content=content)

        elif isinstance(content, list):
            text_content = None
            function_call = None

            for item in content:
                if item["type"] == "text":
                    text_content = item["text"]
                elif item["type"] == "tool_use":
                    function_call = {
                        "name": item["name"],
                        "arguments": item["input"],
                        "id": item.get("id"),
                        "function_call_id": item.get("id"),
                    }
                elif item["type"] == "tool_result":
                    return cls(
                        role="function",
                        content=item["content"],
                        id=item.get("id"),
                        function_call_id=item.get("tool_use_id"),
                    )

            if function_call:
                return cls(
                    role=role,
                    content=text_content,
                    function_call=function_call,
                    function_call_id=function_call["id"],
                )
            else:
                return cls(role=role, content=text_content, function_call_id=None)

        else:
            raise ValueError("Unable to parse anthropic message")

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


class Conversation:
    def __init__(self, messages: list[Message]):
        self.messages = messages

    def to_openai_dict(self) -> list[dict]:
        return [message.to_openai_dict() for message in self.messages]

    def to_anthropic_dict(self) -> list[dict]:
        return [message.to_anthropic_dict() for message in self.messages]
