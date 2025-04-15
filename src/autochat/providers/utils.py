import os

from autochat.model import Message
from autochat.providers.base_provider import APIProvider, BaseProvider


# TODO: should probably exploit default model from provider
def get_provider_and_model(  # TODO: get_provider_and_model ?
    # chat: Autochat, # TODO: make AutochatBase ?
    chat,
    provider_name: str = None,
    model: str = None,
) -> list[str, BaseProvider]:  # TODO: rename
    """
    Returns the correct LLM provider based on a string or env vars.
    """
    from autochat.providers.anthropic import AnthropicProvider
    from autochat.providers.openai import OpenAIProvider
    from autochat.providers.openai_function_legacy import OpenAIProviderFunctionLegacy
    from autochat.providers.openai_function_shim import OpenAIProviderFunctionShim

    if not provider_name:
        provider_name = os.getenv("AUTOCHAT_HOST", "openai")

    if isinstance(provider_name, APIProvider):
        provider_key = provider_name
    elif isinstance(provider_name, str):
        try:
            provider_key = APIProvider(provider_name)
        except ValueError:
            raise ValueError(f"Provider {provider_name} is not a valid provider")
    else:
        raise ValueError(f"Invalid provider: {provider_name}")

    if provider_key == APIProvider.OPENAI:
        if not model:
            model = os.getenv("AUTOCHAT_MODEL", "gpt-4o")
        return OpenAIProvider(chat, model=model), model
    elif provider_key == APIProvider.ANTHROPIC:
        if not model:
            model = os.getenv("AUTOCHAT_MODEL", "claude-3-7-sonnet-latest")
        return AnthropicProvider(chat, model=model), model
    elif provider_key == APIProvider.OPENAI_FUNCTION_SHIM:
        if not model:
            model = os.getenv("AUTOCHAT_MODEL", "o1-preview")
        return OpenAIProviderFunctionShim(chat, model=model), model
    elif provider_key == APIProvider.OPENAI_FUNCTION_LEGACY:
        if not model:
            model = os.getenv("AUTOCHAT_MODEL", "gpt-4o")
        return OpenAIProviderFunctionLegacy(chat, model=model), model
    else:
        raise ValueError(f"Provider {provider_key} is not supported")


def add_empty_function_result(messages: list[Message]) -> list[Message]:
    """
    OpenAI/Anthropic requires a call to have a result message. Not what we want.
    Adjustment for merging or inserting the "function_result":

    - First case: a message with `role="function"` followed by a message with `role="user"`.
      We transform this 'function' message into a part of type 'tool_result' and insert it at the beginning of the following user message.

    - Second case (unchanged): a message with `role="assistant"` containing a `function_call`, followed by a non-`function` message.
      We insert an empty message with `role="function"`.
    """
    for i in range(len(messages) - 1, 0, -1):
        if (
            messages[i - 1].role == "assistant"
            and messages[i - 1].function_call
            and not messages[i].role == "function"
        ):
            # Insert an empty function result
            messages.insert(
                i,
                Message(
                    role="function",
                    name=messages[i - 1].function_call["name"],
                    content="",
                    function_call_id=messages[i - 1].function_call_id,
                ),
            )
    return messages
