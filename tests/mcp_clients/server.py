from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("echo://")
def echo_simple() -> str:
    """Echo a message as a resource"""
    return "Resource echo: hello world"


@mcp.resource("echo2://{message}")
def echo_resource(message: str) -> str:
    """Echo a message as a resource"""
    return f"Resource echo: {message}"
