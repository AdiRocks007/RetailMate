"""
Enhanced AI Integration Tests with Cart Functionality
"""

import asyncio
import sys
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_enhanced_ai_integration():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Testing Enhanced AI Integration with Cart...")
            await session.initialize()
            
            # Test AI status
            print("\n✅ Checking AI status...")
            result = await session.call_tool("get_ai_status", {})
            print("📄 AI Status:")
            print(result.content[0].text)
            
            # Test cart-aware AI recommendations
            print("\n✅ Testing cart-aware AI recommendations...")
            result = await session.call_tool("ai_shopping_assistant", {
                "query": "I need a laptop and accessories for work",
                "user_id": "dummyjson_1"
            })
            ai_response = json.loads(result.content[0].text)
            print("📄 AI Response with Cart Actions:")
            print(f"Response: {ai_response['ai_response'][:300]}...")
            print(f"Suggested cart actions: {len(ai_response.get('suggested_cart_actions', []))}")
            
            # Test cart functionality
            print("\n✅ Testing cart operations...")
            if ai_response.get('suggested_cart_actions'):
                action = ai_response['suggested_cart_actions'][0]
                result = await session.call_tool("add_to_cart", {
                    "product_id": action['product_id'],
                    "user_id": action['user_id'],
                    "ai_reasoning": action['ai_reasoning']
                })
                print("📄 Cart Add Result:")
                print(result.content[0].text)
            
            # Test cart suggestions
            print("\n✅ Testing cart suggestions...")
            result = await session.call_tool("get_cart_suggestions", {
                "user_id": "dummyjson_1"
            })
            print("📄 Cart Suggestions:")
            print(result.content[0].text[:500] + "...")

if __name__ == "__main__":
    asyncio.run(test_enhanced_ai_integration())
