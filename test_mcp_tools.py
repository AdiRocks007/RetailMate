"""
Test enhanced MCP tools with expanded data sources
"""

import asyncio
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_enhanced_tools():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🔗 Initializing enhanced session...")
            await session.initialize()
            
            print("\n✅ Testing enhanced products...")
            result = await session.call_tool("get_enhanced_products", {"limit": 5})
            print("📄 Enhanced products result:")
            print(result.content[0].text)
            
            print("\n✅ Testing all categories...")
            result = await session.call_tool("get_all_categories", {})
            print("📄 Categories result:")
            print(result.content[0].text)
            
            print("\n✅ Testing upcoming holidays...")
            result = await session.call_tool("get_upcoming_holidays", {"days_ahead": 60})
            print("📄 Holidays result:")
            print(result.content[0].text)
            
            print("\n✅ Testing calendar events...")
            result = await session.call_tool("get_calendar_events", {"days_ahead": 14})
            print("📄 Calendar events result:")
            print(result.content[0].text)
            
            print("\n✅ Testing smart recommendations...")
            result = await session.call_tool("get_smart_recommendations", {"user_id": 1})
            print("📄 Smart recommendations result:")
            print(result.content[0].text)
            
            print("\n✅ Testing category mapping...")
            preferences = ["home", "fashion", "jewelry", "electronics", "beauty", "health"]
            result = await session.call_tool("map_user_categories", {"preferences": preferences})
            print("📄 Category mapping result:")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_enhanced_tools())
