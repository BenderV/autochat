from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

FILES = {
    "file1": "Hello world",
    "file2": "Hello world 2",
}


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.resource("files://")
def list_files() -> str:
    """List files in the current directory"""
    return "\n".join(FILES.keys())


@mcp.resource("files://{file_name}")
def get_file(file_name: str) -> str:
    """Get a file"""
    if file_name not in FILES:
        raise ValueError("File " + file_name + " not found")
    return FILES[file_name]
