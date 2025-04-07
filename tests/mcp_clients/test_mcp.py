import asyncio
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


async def handle_server(provider):
    """Example using a single MCP server"""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            agent = Autochat(provider=provider)
            await agent.add_mcp_server(session)
            # Use the async version of ask
            async for message in agent.run_conversation_async(
                "Use calculator to add 1 and 2"
            ):
                print(message.to_terminal())

            async for message in agent.run_conversation_async(
                "List files and then get file1"
            ):
                print(message.to_terminal())


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_mcp_anthropic():
    await handle_server(provider="anthropic")


@pytest.mark.vcr
@pytest.mark.asyncio
async def test_mcp_openai():
    await handle_server(provider="openai")


async def print_mcp_functions(provider):
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            agent = Autochat(provider=provider)
            await agent.add_mcp_server(session)

            print(agent.functions_schema)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", type=str, default="openai")
    args = parser.parse_args()
    asyncio.run(print_mcp_functions(provider=args.provider))
    asyncio.run(handle_server(provider=args.provider))
