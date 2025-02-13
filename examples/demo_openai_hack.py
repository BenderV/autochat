"""
This is a demo of how to use the openai_hack provider,
which is a hacky way to use function calling with OpenAI models.

It is not recommended for production use, but it can be useful for
testing and experimentation.
"""

from autochat import Autochat


def multiply(a: int, b: int) -> int:
    return a * b


# The only model thing you need to do is set the provider to "openai_hack"
agent = Autochat(provider="openai_hack", model="o1-mini")
agent.add_function(multiply)

text = "What is 343354 * 13243343214"
for message in agent.run_conversation(text):
    print(message.to_markdown())
