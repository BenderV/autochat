# AutoChat: OpenAI wrapper to build Conversational AI.

## Description

AutoChat is a Python package that provides an interface for building sophisticated chatbots using the power of OpenAI's GPT-4 model. It simplifies the process of creating conversational agents by providing:

- **Message Handling**: A simple class, `ConversationMessage`, for sending and receiving messages within the conversation.
- **Function Calls**: Capability to handle function calls within the conversation, allowing complex interactions and responses.
- **Template System**: A straightforward text-based template system for defining the behavior of the chatbot, making it easy to customize its responses and actions.

## Highlights

- **ChatGPT**: The main class that orchestrates the conversation with the GPT-4 model. It maintains a history of messages, allows loading and resetting this history, adds functions to the conversation context, and fetches responses from the OpenAI API.
- **ConversationMessage**: A class that encapsulates a message in the conversation. Each instance can represent a user or system message and optionally contain a function call.

The template system allows you to define the chatbot's behavior in a declarative way. Check out an example template file here: [classify_template](./autochat/examples/classify_template.txt).

## Usage

```python
from autochat import ChatGPT

FUNCTIONS_SCHEMA = "functions_schema.json"
TEMPLATE_FILE = "classify_template.txt"  # Look for file in ./examples folder
classifierGPT = ChatGPT.from_template(TEMPLATE_FILE)

def list_items():
    pass

def label_items():
    pass

classifierGPT.add_function(self.list_items, FUNCTIONS_SCHEMA["LIST_ITEMS"])
classifierGPT.add_function(self.label_items, FUNCTIONS_SCHEMA["LABEL_ITEMS"])
classifierGPT.context = "CATEGORIES: \n" + "\n".join(["- " + c for c in categories])

for _ in range(100):   # We don't like infinite loops
    for message in self.classifierGPT.run_conversation(text):
        print(">", message)
    # Ask user for response
    text = input("user:")
```

## Installation

To install the package, you can use pip:

```bash
pip install autochat
```

Please note that this package requires Python 3.6 or later.

## Environment Variables

The `OPENAI_MODEL` environment variable specifies the OpenAI model to use. If not set, it defaults to "gpt-4".

```bash
export OPENAI_MODEL="gpt-4"
export OPENAI_API_KEY=<your-key>
```

## Support

If you encounter any issues or have questions, please file an issue on the GitHub project page.

## License

This project is licensed under the terms of the MIT license.
