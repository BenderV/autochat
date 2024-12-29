import typing
from autochat.model import Message
from autochat.providers.base_provider import BaseProvider


class AutochatBase:  # TODO: rename ?
    instruction: str = (None,)
    examples: typing.Union[list[Message], None]
    messages: typing.Union[list[Message], None]
    context: str
    max_interactions: int
    model: str
    provider: BaseProvider
