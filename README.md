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
- 🙈 Handle caching by default (anthropic model claude-3-7-sonnet-latest)
- ✨ And more features including:
  - Simple template system
  - Easy function and tool integration
  - Flexible instruction and example management
  - Support for images

## Example (search capability)

The library supports function call, handling the back-and-forth between the system and the assistant.

```python
from autochat import Autochat

def search_wikipedia(title: str):
    """Search wikipedia for information"""
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(f"https://en.wikipedia.org/w/index.php?search={title}&title=Special%3ASearch")
    soup = BeautifulSoup(response.text, 'html.parser')
    body_content = soup.find('div', {'id': 'bodyContent'})
    return body_content.text.strip()

classifier_agent = Autochat()
classifier_agent.add_function(search_wikipedia)

text = "Since when is the lastest iphone available?"
for message in classifier_agent.run_conversation(text):
    print(message.to_markdown())

# > ## user
# > Since when is the lastest iphone available?
# > ## assistant
# > search_wikipedia(title=iPhone)
# > ## function
# > Result: (html content)
# > ## assistant
# > The latest flagship iPhone models, the iPhone 16 and 16 Plus, along with the higher-end iPhone 16 Pro and 16 Pro Max, were available as of January 1, 2024.
```

## Quick Start

### Initialize with OpenAI (default)

```python
agent = Autochat(instruction="You are a helpful assistant")
```

### Simple conversation

```python
response = agent.ask("What is the capital of France?")
print(response.content)
```

### Using Anthropic's Claude

```python
agent = Autochat(provider="anthropic")
response = agent.ask("Explain quantum computing in simple terms")
print(response.content)
```

### Run conversation as a generator

```python
for message in agent.run_conversation("Explain quantum computing in simple terms"):
    print(message.to_markdown())
```

### Add a function call as python function

```python
def multiply(a: int, b: int) -> int:
    return a * b

agent = Autochat()
agent.add_function(multiply)
text = "What is 343354 * 13243343214"
for message in agent.run_conversation(text):
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

agent = Autochat()
agent.add_tool(calculator)
for message in agent.run_conversation(
    "What make 343354 * 13243343214"
):
    print(message)
```

## Installation

To install the package, you can use pip:

```bash
pip install 'autochat[all]'
```

## Image support

```python
from autochat import Autochat, Message

from PIL import Image

agent = Autochat()

image = Image.open("examples/image.jpg")
message = Message(role="user", content="describe the image", image=image)
response = agent.ask(message)
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

The `AUTOCHAT_MODEL` environment variable specifies the model to use. If not set, it defaults to "gpt-4o" for openai and "claude-3-7-sonnet-latest" for anthropic.

**We recommend to use Anthropic / claude-3-7-sonnet-latest for agentic behavior.**

```bash
export AUTOCHAT_MODEL="gpt-4o"
export OPENAI_API_KEY=<your-key>
```

or with anthropic

```bash
export AUTOCHAT_MODEL="claude-3-7-sonnet-latest"
export ANTHROPIC_API_KEY=<your-key>
```

Use `AUTOCHAT_HOST` to use alternative provider (openai, anthropic, openpipe, llama_cpp, ...)

## Support

If you encounter any issues or have questions, please file an issue on the GitHub project page.

## License

This project is licensed under the terms of the MIT license.
