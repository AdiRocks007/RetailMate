import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_semantic_search_with_and_without_filter():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Ensure embeddings exist
            print("Generating embeddings for semantic search test...")
            await session.call_tool("generate_embeddings", {"target": "products"})

            # Semantic search without category filter
            print("\nSemantic search without filter:")
            result_no_filter = await session.call_tool("semantic_search", {"query": "smartphone", "top_k": 3})
            print(result_no_filter.content[0].text)

            # Semantic search with category filter 'electronics'
            print("\nSemantic search with category filter 'electronics':")
            result_with_filter = await session.call_tool(
                "semantic_search", {"query": "laptop", "category": "electronics", "top_k": 3}
            )
            print(result_with_filter.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_semantic_search_with_and_without_filter()) 