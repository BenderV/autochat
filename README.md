# AutoChat

AutoChat is an assistant library, that supports OpenAI/Anthropic, to simplify the process of creating interactive agents.

- **Autochat Class**: Conversation wrapper to store instruction, context and messages histories.
- **Message Class**: Message wrapper to handle format/parsing automatically.
- **Function Calls**: Capability to handle function calls within the conversation, allowing complex interactions and responses.
- **Template System**: A straightforward text-based template system for defining the behavior of the chatbot, making it easy to customize its responses and actions.

## Installation

To install the package, you can use pip:

```bash
pip install autochat
```

Please note that this package requires Python 3.6 or later.

## Simple Example

```python
> from autochat import Autochat
> chat = Autochat(instruction="You are a parot")
> chat.ask('Hi my name is Bob')
# Message(role=assistant, content="Hi my name is Bob, hi my name is Bob!")
> chat.ask('Can you tell me my name?')
# Message(role=assistant, content="Your name is Bob, your name is Bob!")
```

## Function Calls Handling

The library supports function calls, handling the back-and-forth between the system and the assistant.

```python
from autochat import Autochat, Message
import json

def label_item(category: str, from_response: Message):
    # TODO: Implement function
    raise NotImplementedError()

with open("./examples/function_label.json") as f:
    FUNCTION_LABEL_ITEM = json.load(f)

classifierGPT = Autochat.from_template("./examples/classify_template.txt")
classifierGPT.add_function(label_item, FUNCTION_LABEL_ITEM)

text = "The new iPhone is out"
for message in classifierGPT.run_conversation(text):
    print(message.to_markdown())

# > ## assistant
# > It's about \"Technology\" since it's about a new iPhone.
# > LABEL_ITEM(category="Technology")
# > ## function
# > NotImplementedError()
# > ## assistant
# > Seem like you didn't implement the function yet.
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
