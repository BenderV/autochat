import os

from autochat.providers.anthropic import AnthropicProvider
from autochat.providers.base_provider import APIProvider, BaseProvider
from autochat.providers.openai import OpenAIProvider
from autochat.providers.openai_hack import OpenAIProviderHack

# from autochat.chat import Autochat


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
    elif provider_key == APIProvider.OPENAI_HACK:
        if not model:
            model = os.getenv("AUTOCHAT_MODEL", "o1-preview")
        return OpenAIProviderHack(chat, model=model), model
    else:
        raise ValueError(f"Provider {provider_key} is not supported")
