import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from autochat import Autochat

currentdir = os.path.dirname(__file__)
server_path = os.path.join(currentdir, "server.py")

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv",
    args=[
        "run",
        "--with",
        "mcp[cli]",
        "mcp",
        "run",
        currentdir + "/server.py",
    ],
)


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_handle_server():
    """Example using a single MCP server"""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # agent = Autochat(provider="anthropic", mcp_servers=[session])
            agent = Autochat(provider="anthropic")
            await agent.add_mcp_server(session)
            # Use the async version of ask
            async for message in agent.run_conversation_async(
                "Use calculator to add 1 and 2"
            ):
                print(message.to_terminal())

