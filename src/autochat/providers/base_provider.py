import typing
from abc import ABC, abstractmethod
from enum import Enum

from autochat.model import Message, MessagePart


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

        # Combine context and last_tools_states if both exist
        context_with_states = self.chat.context or ""
        if self.chat.last_tools_states:
            if context_with_states:
                context_with_states = (
                    context_with_states + "\n\n" + self.chat.last_tools_states
                )
            else:
                context_with_states = self.chat.last_tools_states

        # Add combined context to the first message if it exists
        if context_with_states:
            if isinstance(first_message.content, str):
                first_message.parts[0].content = (
                    context_with_states + "\n" + first_message.parts[0].content
                )
            elif isinstance(first_message.content, list):
                first_message.content = [
                    MessagePart(type="text", content=context_with_states),
                    *first_message.content,
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
