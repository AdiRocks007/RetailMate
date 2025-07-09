"""
Basic MCP server test to isolate the issue
"""

import asyncio
import sys  # ensure we spawn the same Python interpreter

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    # Use the current Python interpreter for subprocess to ensure installed packages are available
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],  # -u for unbuffered I/O
    )

    # Connect to the server over stdio
    async with stdio_client(server_params) as (read_stream, write_stream):
        # Create a client session on those streams
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Initializing session …")
            await session.initialize()
            print("✅ Initialized! Calling get_server_status …")
            result = await session.call_tool("get_server_status", {})
            print("📄 Tool result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
