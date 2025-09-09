from typing import Optional
from autochat.model import Message, MessagePart
from autochat.providers.base_provider import BaseProvider


class AutochatBase:  # TODO: rename ?
    instruction: Optional[str] = None
    examples: list[Message]
    messages: list[Message]
    context: Optional[str]
    max_interactions: int
    model: str
    provider: BaseProvider

    use_tools_only: bool = False
    # Todo: Enhance type of functions_schema
    functions_schema = []

    async def last_tools_states(self) -> Optional[list[MessagePart]]:
        raise NotImplementedError
