"""
RetailMate MCP Server Implementation
Fixed with proper InitializationOptions
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Corrected MCP imports - Added InitializationOptions
from mcp.server import Server
from mcp.server.models import InitializationOptions  # ✅ ADDED THIS IMPORT
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("retailmate-mcp")

class RetailMateMCPServer:
    """Main MCP Server for RetailMate data integration"""
    
    def __init__(self, config_path: str = "backend\\app\\mcp\\config\\mcp_config.json"):
        self.server = Server("retailmate-mcp")
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.tools_registry = {}
        
        # Register server handlers
        self._register_handlers()
        self._register_core_tools()
        
        logger.info("RetailMate MCP Server initialized successfully")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
            return self._default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}. Using defaults.")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for MCP server"""
        return {
            "server": {
                "name": "retailmate-mcp",
                "version": "1.0.0",
                "description": "RetailMate MCP Server for data integration"
            },
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True
            },
            "data_sources": {
                "enabled": ["users", "products", "calendar"]
            }
        }
    
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return available tools"""
            return [
                Tool(
                    name="test_connection",
                    description="Test MCP server connection and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Test message to echo back",
                                "default": "Hello from RetailMate!"
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_server_status",
                    description="Get current server status and configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="list_data_sources",
                    description="List all available data sources for RetailMate",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool execution"""
            try:
                logger.info(f"Executing tool: {name}")
                
                if name == "test_connection":
                    message = arguments.get("message", "Hello from RetailMate MCP!")
                    return [TextContent(
                        type="text",
                        text=f"🚀 Connection Test: {message}"
                    )]
                
                elif name == "get_server_status":
                    status = {
                        "server": self.config["server"]["name"],
                        "version": self.config["server"]["version"],
                        "status": "running",
                        "platform": "Windows",
                        "timestamp": datetime.now().isoformat()
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(status, indent=2)
                    )]
                
                elif name == "list_data_sources":
                    sources = {
                        "user_data": ["dummyjson_users", "github_api"],
                        "product_data": ["fake_store_api", "dummyjson_products"],
                        "calendar_data": ["google_calendar"]
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(sources, indent=2)
                    )]
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    def _register_core_tools(self):
        """Register core tools"""
        self.tools_registry = {
            "test_connection": "Basic connectivity testing",
            "get_server_status": "Server health check",
            "list_data_sources": "Data source inventory"
        }
        logger.info(f"Core tools registered: {list(self.tools_registry.keys())}")
    
    def _check_stdio_availability(self):
        """Check if stdio streams are available"""
        try:
            if sys.stdin is None or sys.stdout is None:
                logger.error("stdin or stdout is None")
                return False
            
            if sys.stdin.closed or sys.stdout.closed:
                logger.error("stdin or stdout is closed")
                return False
                
            logger.info("stdio streams are available")
            return True
            
        except Exception as e:
            logger.error(f"Error checking stdio: {e}")
            return False
    
    async def run(self):
        """Run the MCP server with proper InitializationOptions"""
        try:
            logger.info("Starting RetailMate MCP Server on Windows...")
            
            # Check stdio availability
            if not self._check_stdio_availability():
                logger.error("stdio streams not available, cannot start server")
                return
            
            logger.info("Creating stdio server...")
            
            async with stdio_server() as (read_stream, write_stream):
                logger.info("stdio server created successfully")
                logger.info("Starting MCP server run loop...")
                
                # Create InitializationOptions with proper capabilities
                init_options = InitializationOptions(
                    server_name=self.config["server"]["name"],
                    server_version=self.config["server"]["version"],
                    capabilities=self.server.get_capabilities(
                        self.server.notification_options,
                        {}
                    )
                )
                
                # ✅ FIXED: Pass all three required arguments
                await self.server.run(read_stream, write_stream, init_options)
                
        except KeyboardInterrupt:
            logger.info("Server shutdown requested by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

# Server instance
mcp_server = RetailMateMCPServer()

if __name__ == "__main__":
    try:
        asyncio.run(mcp_server.run())
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server failed to start: {e}")
        import traceback
        traceback.print_exc()
