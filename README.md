# Autochat

[![image](https://img.shields.io/pypi/v/autochat.svg)](https://pypi.python.org/pypi/autochat)
[![image](https://img.shields.io/github/license/BenderV/autochat)](https://github.com/BenderV/autochat/blob/master/LICENSE)
[![Actions status](https://github.com/BenderV/autochat/actions/workflows/test.yml/badge.svg)](https://github.com/BenderV/autochat/actions)

> ⚠️ **Warning**: Since agentic capabilities are evolving fast, expect the API to change.

A powerful yet lightweight Python library for building AI agents with LLMs. Autochat provides a simple and elegant interface to create conversational AI agents that can use tools, call functions, and interact with various LLM providers.

![image](https://www-cdn.anthropic.com/images/4zrzovbb/website/58d9f10c985c4eb5d53798dea315f7bb5ab6249e-2401x1000.png)

## Key Features

- 🤝 **Multi-Provider Support**: Works with OpenAI, Anthropic, and custom providers
- 🛠️ **Tool Integration**: Transform Python functions and classes into AI-accessible tools
- 🔁 **Streaming Conversations**: Run conversations as generators for real-time interaction
- 🧠 **Smart Caching**: Built-in response caching (especially for Anthropic's Claude models)
- 🖼️ **Image Support**: Process and analyze images with vision-capable models
- 📝 **Template System**: Define agent behavior with simple markdown-like templates
- 🔄 **Async Support**: Full async/await support for non-blocking operations
- 🌐 **MCP Integration**: Connect to Model Context Protocol servers for extended capabilities
- 📊 **Function Calling**: Seamless back-and-forth between AI and your functions
- 🎯 **Agent Architecture**: Perfect for building sophisticated AI agents and assistants

## Real-World Example: Code Development Agent

Autochat excels at building development agents. Here's how [autocode](../autocode/) uses autochat to create an AI developer:

```python
from autochat import Autochat
from autocode.code_editor import CodeEditor
from autocode.terminal import Terminal
from autocode.git import Git

# Create a developer agent
agent = Autochat(
    instruction="""You are a developer agent equipped with tools to:
    1. Edit code files
    2. Run terminal commands  
    3. Manage git operations
    4. Test and debug applications""",
    provider="anthropic",
    model="claude-3-5-sonnet-latest",
    name="Developer"
)

# Add development tools
code_editor = CodeEditor()
agent.add_tool(code_editor)

terminal = Terminal()
agent.add_tool(terminal)

git = Git()
agent.add_tool(git)

# The agent can now autonomously develop, test, and deploy code
for message in agent.run_conversation("Create a FastAPI hello world app with tests"):
    print(message.to_markdown())
```


## Installation

Install autochat with all providers and features:

```bash
pip install 'autochat[all]'
```

Or install with specific providers:

```bash
# OpenAI only
pip install 'autochat[openai]'

# Anthropic only  
pip install 'autochat[anthropic]'

# With MCP support (Python 3.10+)
pip install 'autochat[mcp]'
```

## Quick Start

```python
from autochat import Autochat

# Basic usage
agent = Autochat(instruction="You are a helpful assistant")
response = agent.ask("What is the capital of France?")
print(response.content)

# With function calling
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

agent.add_function(multiply)
for message in agent.run_conversation("What is 25 * 47?"):
    print(message.to_markdown())

# With Anthropic (recommended for agents)
agent = Autochat(provider="anthropic", model="claude-3-5-sonnet-latest")
```

## Advanced Features

### Image Support

```python
from autochat import Autochat, Message
from PIL import Image

agent = Autochat()
image = Image.open("examples/image.jpg")
message = Message(role="user", content="Describe this image", image=image)
response = agent.ask(message)
```

### Template System

```python
# Load agent from markdown template
agent = Autochat.from_template("./agent_template.md")
```

### Async Support

```python
# Async operations
response = await agent.ask_async("Hello")
async for message in agent.run_conversation_async("Help me code"):
    print(message.content)
```

## Configuration

```bash
# Set up your API keys
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Choose your model (optional)
export AUTOCHAT_MODEL="claude-3-5-sonnet-latest"  # or gpt-4o
```

💡 **Recommendation**: Use Anthropic's Claude models for complex agentic behavior and tool use.

## Use Cases

- **🤖 AI Assistants**: Build conversational assistants with tool access
- **🛠️ Development Agents**: Create agents that can code, test, and deploy (like autocode)
- **📊 Data Analysis**: Agents that can query databases, generate reports, visualize data
- **🌐 Web Automation**: Agents that interact with web APIs and services
- **📋 Task Automation**: Automate complex workflows with AI decision-making
- **🎯 Custom Tools**: Integrate your existing Python tools with AI

## Documentation

- [API Reference](docs/api-reference.md) - Complete API documentation
- [Examples](examples/) - More example implementations
- [Provider Guide](docs/providers.md) - Working with different LLM providers
- [Tool Development](docs/tool-development.md) - Creating custom tools
- [Best Practices](docs/best-practices.md) - Tips for building robust agents

## Support

If you encounter any issues or have questions, please file an issue on the GitHub project page.

## License

This project is licensed under the terms of the MIT license.
