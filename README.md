# AutoChat

[![image](https://img.shields.io/pypi/v/autochat.svg)](https://pypi.python.org/pypi/autochat)
[![image](https://img.shields.io/pypi/l/autochat.svg)](https://github.com/BenderV/autochat/blob/master/LICENSE)
[![Actions status](https://github.com/astral-sh/ruff/workflows/CI/badge.svg)](https://github.com/astral-sh/ruff/actions)

The LLM library for the Agent era, on top of OpenAI/Anthropic.

Add function and tool as easy as ... adding a python function.
Give instructions to the assistant, and add examples.
Let the assistant do the work.

## Installation

To install the package, you can use pip:

```bash
pip install autochat
```

Please note that this package requires Python 3.6 or later.

## Function Call (as python function)

The library supports function call, handling the back-and-forth between the system and the assistant.

```python
from autochat import Autochat, Message
import requests

def search_top_result(query: str):
    response = requests.get(f"https://google.com/search?q={query}")
    return response.text

classifierGPT = Autochat(instruction="You are a helpful assistant that can search the web for information")
classifierGPT.add_function(search_top_result)

text = "since when is the lastest iphone available?"
for message in classifierGPT.run_conversation(text):
    print(message.to_markdown())

# > ## assistant
# > search_top_result(query=next iphone release date)
# > ## function
# > (html content)
# > ## assistant
# > The latest iPhone models, iPhone 14, iPhone 14 Plus, iPhone 14 Pro, and iPhone 14 Pro Max, were released on September 16, 2022.

```

## Simple Example

```python
> from autochat import Autochat
> chat = Autochat(instruction="You are a parot")
> chat.ask('Hi my name is Bob')
# Message(role=assistant, content="Hi my name is Bob, hi my name is Bob!")
> chat.ask('Can you tell me my name?')
# Message(role=assistant, content="Your name is Bob, your name is Bob!")
```

## Template System

We provide a simple template system for defining the behavior of the chatbot, using markdown-like syntax.

```
## system
You are a parrot

## user
Hi my name is Bob

## assistant
Hi my name is Bob, hi my name is Bob!

## user
Can you tell me my name?

## assistant
Your name is Bob, your name is Bob!
```

You can then load the template file using the `from_template` method:

```python
parrotGPT = Autochat.from_template("./parrot_template.txt")
```

The template system also supports function calls. Check out the [examples/demo_label.py](examples/demo_label.py) for a complete example.

## Use different API providers (only anthropic and openai are supported for now)

Default provider is openai.

Anthropic:

```python
chat = Autochat(provider="anthropic")
```

## Environment Variables

The `AUTOCHAT_MODEL` environment variable specifies the model to use. If not set, it defaults to "gpt-4-turbo".

```bash
export AUTOCHAT_MODEL="gpt-4-turbo"
export OPENAI_API_KEY=<your-key>
```

or with anthropic

```bash
export AUTOCHAT_MODEL="claude-3-opus"
export ANTHROPIC_API_KEY=<your-key>
```

Use `AUTOCHAT_HOST` to use alternative provider (openai, anthropic, openpipe, llama_cpp, ...)

## Support

If you encounter any issues or have questions, please file an issue on the GitHub project page.

## License

This project is licensed under the terms of the MIT license.
