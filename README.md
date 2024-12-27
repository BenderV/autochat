# Autochat

[![image](https://img.shields.io/pypi/v/autochat.svg)](https://pypi.python.org/pypi/autochat)
[![image](https://img.shields.io/github/license/BenderV/autochat)](https://github.com/BenderV/autochat/blob/master/LICENSE)
[![Actions status](https://github.com/BenderV/autochat/actions/workflows/test.yml/badge.svg)](https://github.com/BenderV/autochat/actions)

A lightweight Python library to build AI agents with LLMs.

![image](https://www-cdn.anthropic.com/images/4zrzovbb/website/58d9f10c985c4eb5d53798dea315f7bb5ab6249e-2401x1000.png)

## Key Features

- 🤝 Support for multiple LLM providers (OpenAI and Anthropic)
- 🐍 Transform python function or class into a tool
- 🔁 Run conversation as a generator.
- 🙈 Handle caching by default (anthropic model claude-3-5-sonnet-20240620)
- ✨ And more features including:
  - Simple template system
  - Easy function and tool integration
  - Flexible instruction and example management
  - Support for images

## Quick Start

### Initialize with OpenAI (default)

```python
chat = Autochat(instruction="You are a helpful assistant")
```

### Simple conversation

```python
response = chat.ask("What is the capital of France?")
print(response.content)
```

### Using Anthropic's Claude

```python
chat = Autochat(provider="anthropic")
response = chat.ask("Explain quantum computing in simple terms")
print(response.content)
```

### Run conversation as a generator

```python
for message in chat.run_conversation("Explain quantum computing in simple terms"):
    print(message.to_markdown())
```

### Add a function call as python function

```python
def search_top_result(query: str):
    import requests
    response = requests.get(f"https://google.com/search?q={query}")
    return response.text

chatGPT = Autochat()
chatGPT.add_function(search_top_result)
text = "since when is the lastest iphone available?"
for message in chatGPT.run_conversation(text):
    print(message.to_markdown())
```

### Add a Class as a tool

```python
from autochat import Autochat

class Calculator:
    def add(self, a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b

calculator = Calculator()

chat = Autochat()
chat.add_tool(calculator)
for message in chat.run_conversation(
    "What make 343354 * 13243343214"
):
    print(message)
```

## Installation

To install the package, you can use pip:

```bash
pip install 'autochat[all]'
```

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

## Image support

```python
from autochat import Autochat, Message

from PIL import Image

chat = Autochat()

image = Image.open("examples/image.jpg")
message = Message(role="user", content="describe the image", image=image)
response = chat.ask(message)
print(response.to_markdown())
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

## Environment Variables

The `AUTOCHAT_MODEL` environment variable specifies the model to use. If not set, it defaults to "gpt-4o" for openai and "claude-3-5-sonnet-20240620" for anthropic.

**We recommend to use Anthropic / claude-3-5-sonnet-20240620 for agentic behavior.**

```bash
export AUTOCHAT_MODEL="gpt-4o"
export OPENAI_API_KEY=<your-key>
```

or with anthropic

```bash
export AUTOCHAT_MODEL="claude-3-5-sonnet-20240620"
export ANTHROPIC_API_KEY=<your-key>
```

Use `AUTOCHAT_HOST` to use alternative provider (openai, anthropic, openpipe, llama_cpp, ...)

## Support

If you encounter any issues or have questions, please file an issue on the GitHub project page.

## License

This project is licensed under the terms of the MIT license.
