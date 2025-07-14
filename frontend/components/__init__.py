import sys
import asyncio
if sys.platform == "win32":
    try:
        from asyncio import WindowsProactorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    except ImportError:
        pass
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def fetch_products_from_mcp(limit=20, category=None, search=None):
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )
    args = {"limit": limit}
    if category:
        args["category"] = category
    if search:
        args["search"] = search
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("get_enhanced_products", args)
            # result.content[0].text is a JSON string with 'products' key
            import json
            data = json.loads(result.content[0].text)
            return data.get("products", [])

def get_products(limit=20, category=None, search=None):
    # Streamlit is not async, so we need to run the async function in a blocking way
    return asyncio.run(fetch_products_from_mcp(limit, category, search))
