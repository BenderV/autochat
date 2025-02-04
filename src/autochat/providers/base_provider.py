from autochat.model import Message, MessagePart
from abc import ABC, abstractmethod
from enum import Enum
import typing


class APIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENAI_HACK = "openai_hack"


class BaseProvider(ABC):
    def prepare_messages(
        self,
        transform_function: typing.Callable,
        transform_list_function: typing.Callable = lambda x: x,
    ) -> list[dict]:
        """Prepare messages for API requests using a transformation function."""
        first_message = self.chat.messages[0]
        if self.chat.context:
            # Add context to the first message
            if isinstance(first_message.content, str):
                first_message.parts[0].content = (
                    self.chat.context + "\n" + first_message.parts[0].content
                )
            elif isinstance(first_message.content, list):
                first_message.content = [
                    MessagePart(type="text", content=self.chat.context),
                    *first_message.content,
                ]

        if self.chat.last_context:
            # Add last context to the beginning of the last message
            last_message = self.chat.messages[-1]
            if isinstance(last_message.content, str):
                last_message.parts[0].content = (
                    self.chat.last_context + "\n" + last_message.parts[0].content
                )
            elif isinstance(last_message.content, list):
                last_message.content = [
                    MessagePart(type="text", content=self.chat.last_context),
                    *last_message.content,
                ]

        messages = self.chat.examples + [first_message] + self.chat.messages[1:]
        transform_list_function(messages)
        return [transform_function(m) for m in messages]

    @abstractmethod
    def fetch(self, **kwargs) -> Message:
        """
        Given a chat context, returns a single new Message from the LLM.
        """
        pass
