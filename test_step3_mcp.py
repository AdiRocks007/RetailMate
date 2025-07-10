"""
Test Step 3 data processing tools
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_step3_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Testing Step 3 data processing...")
            await session.initialize()
            
            print("\n✅ Testing data normalization...")
            result = await session.call_tool("normalize_all_data", {"include_embeddings": False})
            print("📄 Normalization result:")
            print(result.content[0].text)
            
            print("\n✅ Testing embedding generation...")
            result = await session.call_tool("generate_embeddings", {"target": "products"})
            print("📄 Embedding result:")
            print(result.content[0].text)
            
            print("\n✅ Testing semantic search...")
            result = await session.call_tool("semantic_search", {"query": "smartphone", "top_k": 3})
            print("📄 Search result:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_step3_tools())
