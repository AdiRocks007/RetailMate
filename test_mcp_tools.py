"""
Test enhanced MCP tools with API integration
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Initializing session...")
            await session.initialize()
            
            print("✅ Testing get_user_data tool...")
            result = await session.call_tool("get_user_data", {"user_id": 1})
            print("📄 User data result:")
            print(result.content[0].text)
            
            print("\n✅ Testing search_products tool...")
            result = await session.call_tool("search_products", {"query": "shirt", "limit": 3})
            print("📄 Product search result:")
            print(result.content[0].text)
            
            print("\n✅ Testing product recommendations...")
            result = await session.call_tool("get_product_recommendations", {"user_id": 1})
            print("📄 Recommendations result:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_tools())
