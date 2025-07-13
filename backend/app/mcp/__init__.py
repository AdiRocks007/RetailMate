"""
RetailMate MCP Integration Package
Model Context Protocol implementation for data source management
Compatible with MCP Specification v1.0
"""

from .server import RetailMateMCPServer, mcp_server
from .protocol_handler import MCPProtocolHandler, protocol_handler

__version__ = "1.0.0"
__author__ = "RetailMate Team"
__platform__ = "Windows"
__mcp_version__ = "1.0.0"

__all__ = [
    "RetailMateMCPServer",
    "mcp_server",
    "MCPProtocolHandler", 
    "protocol_handler"
]

# Package-level configuration
MCP_CONFIG = {
    "server_name": "retailmate-mcp",
    "version": __version__,
    "description": "AI-powered shopping assistant with emotion-aware, calendar-integrated data management",
    "platform": __platform__,
    "mcp_specification": __mcp_version__,
    "compatibility": {
        "json_rpc": "2.0",
        "python": ">=3.9",
        "mcp_sdk": ">=1.0.0"
    }
}
