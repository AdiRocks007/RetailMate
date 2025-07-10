"""
Test complete AI integration with RetailMate
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_ai_integration():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Testing AI Integration...")
            await session.initialize()
            
            print("\n✅ Checking AI status...")
            result = await session.call_tool("get_ai_status", {})
            print("📄 AI Status:")
            print(result.content[0].text)
            
            print("\n✅ Testing AI shopping assistant...")
            result = await session.call_tool("ai_shopping_assistant", {
                "query": "I need a laptop for programming work",
                "user_id": "dummyjson_1"
            })
            print("📄 AI Shopping Recommendation:")
            print(result.content[0].text)
            
            print("\n✅ Testing AI event planner...")
            result = await session.call_tool("ai_event_planner", {
                "event_id": "event_25"
            })
            print("📄 AI Event Planning:")
            print(result.content[0].text)
            
            print("\n✅ Testing AI chat...")
            result = await session.call_tool("ai_chat", {
                "message": "Hello! I'm looking for a birthday gift for my friend",
                "conversation_id": "test_conv_1",
                "user_id": "dummyjson_1"
            })
            print("📄 AI Chat Response:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_ai_integration())
