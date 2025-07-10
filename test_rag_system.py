"""
Test complete RAG system functionality
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_rag_system():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Testing RAG System...")
            await session.initialize()
            
            print("\n✅ Initializing vector store...")
            result = await session.call_tool("initialize_vector_store", {"reset_existing": True})
            print("📄 Vector store initialization:")
            print(result.content[0].text[:300] + "...")
            
            print("\n✅ Testing RAG search...")
            result = await session.call_tool("rag_search", {
                "query": "I need a smartphone for work", 
                "user_id": "dummyjson_1"
            })
            print("📄 RAG search result:")
            print(result.content[0].text[:400] + "...")
            
            print("\n✅ Testing event shopping assistant...")
            result = await session.call_tool("event_shopping_assistant", {"event_id": "event_25"})
            print("📄 Event shopping result:")
            print(result.content[0].text[:400] + "...")
            
            print("\n✅ Getting vector store stats...")
            result = await session.call_tool("get_vector_store_stats", {})
            print("📄 Vector store stats:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_rag_system())
