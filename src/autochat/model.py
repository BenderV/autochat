import json
import typing
import base64
from io import BytesIO
from typing import Literal

from PIL import Image as PILImage


class FunctionCallParsingError(Exception):
    def __init__(self, id, function_call):
        self.id = id
        self.function_call = function_call

    def __str__(self):
        return f"Invalid function_call: {self.obj.function_call}"


class Image:
    def __init__(self, image: PILImage.Image):
        if not isinstance(image, PILImage.Image):
            raise TypeError("image must be an instance of PIL.Image.Image")
        self.image = image

    def resize(self, size: tuple[int, int]):
        try:
            self.image = self.image.resize(size)
        except Exception as e:
            raise ValueError(f"Failed to resize image: {e}")

    def to_base64(self):
        try:
            buffered = BytesIO()
            self.image.save(buffered, format=self.image.format)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return img_str
        except Exception as e:
            raise ValueError(f"Failed to convert image to base64: {e}")

    @classmethod
    def from_bytes(cls, img_bytes: bytes):
        return cls(PILImage.open(BytesIO(img_bytes)))

    def to_bytes(self):
        try:
            buffered = BytesIO()
            self.image.save(buffered, format=self.image.format)
            return buffered.getvalue()
        except Exception as e:
            raise ValueError(f"Failed to convert image to bytes: {e}")

    @property
    def format(self):
        return "image/" + self.image.format.lower()


class MessagePart:
    def __init__(
        self,
        # TODO: function_result should be named "tool_result" ?
        type: Literal["text", "image", "function_call", "function_result"],
        content: typing.Optional[str] = None,  # TODO: should be named "text" !
        image: typing.Optional[PILImage.Image] = None,
        function_call: typing.Optional[dict] = None,
        function_call_id: typing.Optional[str] = None,
        data: typing.Optional[dict] = None,
    ) -> None:
        self.type = type
        self.content = content
        self.image = Image(image) if image else None
        self.function_call = function_call
        self.function_call_id = function_call_id
        self.data = data  # TODO: remove

    def to_openai_dict(self) -> dict:
        if self.type == "text":
            return {
                "type": "text",
                "text": self.content,
            }
        elif self.type == "image":
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.image.format};base64,{self.image.to_base64()}"
                },
            }
        elif self.type == "function_call":
            return {
                "name": self.function_call["name"],
                "arguments": json.dumps(self.function_call["arguments"]),
            }
        elif self.type == "function_result":
            return {
                "type": "text",
                "text": self.content,
            }

        return {}

    def to_anthropic_dict(self) -> dict:
        if self.type == "text":
            return {
                "type": "text",
                "text": self.content,
            }
        elif self.type == "image":
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.image.format,
                    "data": self.image.to_base64(),
                },
            }
        elif self.type == "function_call":
            return {
                "type": "tool_use",
                "id": self.function_call_id,
                "name": self.function_call["name"],
                "input": self.function_call["arguments"],
            }
        elif self.type == "function_result":
            return {
                "type": "tool_result",
                "tool_use_id": self.function_call_id,
                "content": self.content,
            }
        return {}


class Message:
    role: Literal["user", "assistant", "function"]
    parts: list[MessagePart]
    name: typing.Optional[str] = None
    id: typing.Optional[int] = None

    def __init__(
        self,
        role: Literal["user", "assistant", "function"],
        content: str = None,
        name: typing.Optional[str] = None,
        function_call: typing.Optional[dict] = None,
        id: typing.Optional[int] = None,
        function_call_id: typing.Optional[str] = None,
        image: typing.Optional[PILImage.Image] = None,
        parts: typing.Optional[list[MessagePart]] = [],
    ) -> None:
        self.role = role
        self.name = name
        self.id = id

        # Can't have both parts and content/image/function_call
        if parts and (content or image or function_call):
            raise ValueError("Can't have both parts and content/image/function_call")

        if parts:
            self.parts = parts
        else:
            self.parts = []
            if role != "function":
                if content:
                    self.parts.append(MessagePart(type="text", content=content))
                if image:
                    self.parts.append(MessagePart(type="image", image=image))
                if function_call:
                    self.parts.append(
                        MessagePart(
                            type="function_call",
                            function_call=function_call,
                            function_call_id=function_call_id,
                        )
                    )
            else:
                self.parts.append(
                    MessagePart(
                        type="function_result",
                        content=content,
                        function_call_id=function_call_id,
                    )
                )

    @property
    def content(self) -> str:
        """
        If one part text, then provide the sugar syntax
        # If multiple parts text, then throw an error
        """
        if self.role == "function":
            results = [
                part.content for part in self.parts if part.type == "function_result"
            ]
            assert (
                len(results) == 1
            ), "Function messages should have exactly one function_result part"
            return results[0]
        # 1. get all text parts
        text_parts = [part.content for part in self.parts if part.type == "text"]
        # 2. verify that there is only one text part
        if not text_parts:
            return None
        if len(text_parts) > 1:
            raise ValueError("Message has multiple text parts")
        # 3. return the result
        return text_parts[0]

    @content.setter
    def content(self, value: str):
        """
        If one part text, then set the sugar syntax
        If multiple parts text, then throw an error
        """
        if self.role == "function":
            raise ValueError("Function messages cannot have content")
        # 1. get all text parts
        text_parts = [part.content for part in self.parts if part.type == "text"]
        # 2. verify that there is only one text part
        if not text_parts:
            raise ValueError("Message has no text part")
        if len(text_parts) > 1:
            raise ValueError("Message has multiple text parts")
        # 3. set the sugar syntax
        self.parts[0].content = value

    @property
    def function_call(self) -> typing.Optional[dict]:
        """
        If one part, then provide the sugar syntax
        """
        # 1. get all function_call parts
        function_call_parts = [
            part.function_call for part in self.parts if part.type == "function_call"
        ]
        # 2. verify that there is only one function_call part
        if not function_call_parts:
            return None
        if len(function_call_parts) > 1:
            raise ValueError("Message has multiple function_call parts")
        # 3. return the result
        return function_call_parts[0]

    @property
    def function_call_id(self) -> typing.Optional[str]:
        """
        If one part, then provide the sugar syntax
        """
        # 1. get all function_call_id parts
        function_call_parts = [
            part.function_call_id
            for part in self.parts
            if part.type in ["function_call", "function_result"]
        ]
        # 2. verify that there is only one function_call_id part
        if not function_call_parts:
            return None
        if len(function_call_parts) > 1:
            raise ValueError("Message has multiple function_call parts")
        # 3. return the result
        return function_call_parts[0]

    @property
    def image(self) -> typing.Optional[PILImage.Image]:
        """
        If one part, then provide the sugar syntax
        """
        # 1. get all image parts
        image_parts = [part.image for part in self.parts if part.type == "image"]
        # 2. verify that there is only one image part
        if not image_parts:
            return None
        if len(image_parts) > 1:
            raise ValueError("Message has multiple image parts")
        # 3. return the result
        return image_parts[0]

    def to_openai_dict(self) -> dict:
        res = {
            "role": self.role,
            "content": [],
        }

        for part in self.parts:
            if part.type == "function_call" and self.role == "assistant":
                res["function_call"] = part.to_openai_dict()
            elif part.type == "function_call" and self.role == "user":
                # Workaround: If the user is triggering a function, we add it's name and arguments to the content
                res["content"] = (
                    part.function_call["name"]
                    + ":"
                    + json.dumps(part.function_call["arguments"])
                )
            else:
                res["content"].append(part.to_openai_dict())

        if self.name:
            res["name"] = self.name

        return res

    def to_anthropic_dict(self) -> dict:
        res = {
            "role": self.role if self.role in ["user", "assistant"] else "user",
            "content": [],
        }

        for part in self.parts:
            res["content"].append(part.to_anthropic_dict())

        return res

    @classmethod
    def from_openai_dict(
        cls,
        role: str,
        content: str,
        function_call: typing.Optional[dict] = None,
        id: typing.Optional[str] = None,
    ):
        # We need to unquote the arguments
        function_call_dict = None
        if function_call:
            try:
                function_call_dict = {
                    "name": function_call.name,
                    "arguments": json.loads(function_call.arguments),
                }
            except json.decoder.JSONDecodeError:
                raise FunctionCallParsingError(id, function_call)

        obj = cls(role=role, content=content, function_call=function_call_dict, id=id)
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
        text = f"Message(role={self.role}, parts=["
        for part in self.parts:
            text += f"{part.type}, "
        return text[:-2] + "])"

    def to_markdown(self) -> str:
        text = f"## {self.role}\n"
        for part in self.parts:
            if part.type == "text":
                text += part.content + "\n"
            elif part.type == "function_call":
                text += f"> {part.function_call['name']}({', '.join([f'{k}={v}' for k, v in part.function_call['arguments'].items()])})\n"
            elif part.type == "function_result":
                text += f"> Result: {part.content}\n"
        if not self.parts:
            raise ValueError("Message should have at least one part")
        return text


class Conversation:
    def __init__(self, messages: list[Message]):
        self.messages = messages

    def to_openai_dict(self) -> list[dict]:
        return [message.to_openai_dict() for message in self.messages]

    def to_anthropic_dict(self) -> list[dict]:
        return [message.to_anthropic_dict() for message in self.messages]
