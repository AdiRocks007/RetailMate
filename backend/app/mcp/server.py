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

from ..services.api_clients.user_apis.dummyjson_client import DummyJSONUsersClient
from ..services.api_clients.product_apis.fake_store_client import FakeStoreAPIClient
from ..services.api_clients.product_apis.dummyjson_products_client import DummyJSONProductsClient
from ..services.api_clients.holiday_apis.holiday_client import HolidayAPIClient
from ..services.api_clients.calendar_apis.calendar_client import CalendarClient
from ..services.data_processing.data_normalizer import DataNormalizer
from ..services.embeddings.embedding_service import EmbeddingService
from ..services.rag.vector_store.chroma_store import ChromaVectorStore
from ..services.rag.context.context_builder import ContextBuilder
from ..services.ai.ollama.ollama_service import OllamaService
from ..services.cart.cart_service import CartService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("retailmate-mcp")

# Mapping between user preference categories and actual product categories
USER_PREFERENCE_CATEGORY_MAPPING = {
    "home": ["home", "home-decoration", "furniture", "lighting"],
    "fashion": ["men's clothing", "women's clothing", "tops", "womens-dresses", "womens-shoes", "mens-shirts", "mens-shoes"],
    "jewelry": ["jewelery", "womens-jewellery"],
    "electronics": ["electronics", "smartphones", "laptops"],
    "beauty": ["fragrances", "skincare"],
    "health": ["groceries"]
}

def map_user_preference_to_categories(user_preferences: List[str], available_categories: List[str]) -> Dict[str, List[str]]:
    """Map user preference categories to actual available product categories."""
    mapping_result: Dict[str, List[str]] = {}
    for pref in user_preferences:
        key = pref.lower()
        mapped = USER_PREFERENCE_CATEGORY_MAPPING.get(key, [])
        valid = [cat for cat in mapped if cat in available_categories]
        mapping_result[pref] = valid
    return mapping_result

class RetailMateMCPServer:
    """Main MCP Server for RetailMate data integration"""
    
    def __init__(self, config_path: str = "backend\\app\\mcp\\config\\mcp_config.json"):
        self.server = Server("retailmate-mcp")
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.tools_registry = {}
        
        # Register server handlers
        self._register_handlers()
        # Register core tools
        self._register_core_tools()
        # Initialize a single CartService instance for persistent cart state
        self.cart_service = CartService()
        
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
                ),
                Tool(
                    name="get_user_data",
                    description="Get user data from DummyJSON API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID to fetch",
                                "minimum": 1
                            },
                            "include_preferences": {
                                "type": "boolean",
                                "description": "Include derived shopping preferences",
                                "default": True
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="search_products",
                    description="Search products using Fake Store API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for products"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_product_recommendations",
                    description="Get personalized product recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID for personalization",
                                "minimum": 1
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_enhanced_products",
                    description="Get products from DummyJSON Products API with more variety",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Product category to filter by (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of products",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "search": {
                                "type": "string",
                                "description": "Search query (optional)"
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_all_categories",
                    description="Get all available product categories from all APIs",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_upcoming_holidays",
                    description="Get upcoming holidays and shopping suggestions",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "country": {
                                "type": "string",
                                "description": "Country code (e.g., US, UK, CA)",
                                "default": "US"
                            },
                            "days_ahead": {
                                "type": "integer",
                                "description": "Look ahead this many days",
                                "default": 90,
                                "minimum": 1,
                                "maximum": 365
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_calendar_events",
                    description="Get upcoming calendar events that might need shopping",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_ahead": {
                                "type": "integer",
                                "description": "Look ahead this many days",
                                "default": 14,
                                "minimum": 1,
                                "maximum": 90
                            },
                            "shopping_only": {
                                "type": "boolean",
                                "description": "Only return events that need shopping",
                                "default": True
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_smart_recommendations",
                    description="Get intelligent recommendations based on user, calendar, and holidays",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "integer",
                                "description": "User ID for personalization",
                                "minimum": 1
                            },
                            "include_calendar": {
                                "type": "boolean",
                                "description": "Include calendar-based recommendations",
                                "default": True
                            },
                            "include_holidays": {
                                "type": "boolean",
                                "description": "Include holiday-based recommendations",
                                "default": True
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="map_user_categories",
                    description="Map user preference categories to actual available product categories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "preferences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of user preference categories to map"
                            }
                        },
                        "required": ["preferences"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="semantic_search",
                    description="Search products using semantic similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query text"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by category (optional)"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="normalize_all_data",
                    description="Normalize all data from APIs into unified models",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_embeddings": {
                                "type": "boolean",
                                "description": "Generate embeddings after normalization",
                                "default": True
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="generate_embeddings",
                    description="Generate embeddings for products and users",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "What to embed: products, users, or both",
                                "enum": ["products", "users", "both"],
                                "default": "both"
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="initialize_vector_store",
                    description="Initialize ChromaDB with products and users",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "reset_existing": {
                                "type": "boolean",
                                "description": "Reset existing collections",
                                "default": False
                            }
                        },
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="rag_search",
                    description="RAG-powered product search with context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID for personalization (optional)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="event_shopping_assistant",
                    description="Get shopping suggestions for calendar events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_id": {
                                "type": "string",
                                "description": "Calendar event ID"
                            }
                        },
                        "required": ["event_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_vector_store_stats",
                    description="Get ChromaDB collection statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="ai_shopping_assistant",
                    description="AI-powered shopping recommendations using Ollama",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "User's shopping question or request"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID for personalization (optional)"
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="ai_event_planner",
                    description="AI event shopping planner using calendar context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_id": {
                                "type": "string",
                                "description": "Calendar event ID"
                            }
                        },
                        "required": ["event_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="ai_chat",
                    description="Conversational AI shopping assistant",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "User message"
                            },
                            "conversation_id": {
                                "type": "string",
                                "description": "Conversation identifier"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID (optional)"
                            }
                        },
                        "required": ["message", "conversation_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_ai_status",
                    description="Get Ollama model status and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="add_to_cart",
                    description="Add product to user's cart with AI reasoning",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "Product ID to add to cart"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity to add",
                                "default": 1
                            },
                            "ai_reasoning": {
                                "type": "string",
                                "description": "AI explanation for why this product is recommended"
                            }
                        },
                        "required": ["product_id", "user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="remove_from_cart",
                    description="Remove product from user's cart",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "string",
                                "description": "Product ID to remove"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID"
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "Quantity to remove (optional - removes all if not specified)"
                            }
                        },
                        "required": ["product_id", "user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_cart_contents",
                    description="Get user's complete cart contents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID"
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="get_cart_suggestions",
                    description="Get AI-powered cart suggestions and optimizations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID"
                            },
                            "query": {
                                "type": "string",
                                "description": "Optional query for specific suggestions"
                            }
                        },
                        "required": ["user_id"],
                        "additionalProperties": False
                    }
                ),
                Tool(
                    name="clear_cart",
                    description="Clear user's cart completely",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "User ID"
                            }
                        },
                        "required": ["user_id"],
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
                
                elif name == "get_user_data":
                    user_id = arguments.get("user_id")
                    include_preferences = arguments.get("include_preferences", True)
                    try:
                        async with DummyJSONUsersClient() as client:
                            if include_preferences:
                                user_data = await client.get_user_preferences(user_id)
                            else:
                                user_data = await client.get_user_by_id(user_id)
                        return [TextContent(
                            type="text",
                            text=json.dumps(user_data, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error fetching user data: {str(e)}"
                        )]
                
                elif name == "search_products":
                    query = arguments.get("query")
                    category = arguments.get("category")
                    limit = arguments.get("limit", 10)
                    try:
                        async with FakeStoreAPIClient() as client:
                            products = await client.search_products(query, category)
                            products = products[:limit]
                        return [TextContent(
                            type="text",
                            text=json.dumps(products, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error searching products: {str(e)}"
                        )]
                
                elif name == "get_product_recommendations":
                    user_id = arguments.get("user_id")
                    try:
                        async with DummyJSONUsersClient() as user_client:
                            user_preferences = await user_client.get_user_preferences(user_id)
                        async with FakeStoreAPIClient() as product_client:
                            recommendations = await product_client.get_product_recommendations(user_preferences)
                        result = {
                            "user_id": user_id,
                            "recommendations": recommendations,
                            "total_found": len(recommendations)
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error generating recommendations: {str(e)}"
                        )]
                elif name == "map_user_categories":
                    # Map user preference categories to actual categories
                    preferences = arguments.get("preferences", [])
                    try:
                        # Fetch all available categories
                        async with FakeStoreAPIClient() as fake_store_client:
                            fake_store_categories = await fake_store_client.get_categories()
                        async with DummyJSONProductsClient() as dummyjson_client:
                            raw_dummyjson_categories = await dummyjson_client.get_categories()
                        # Clean DummyJSON categories
                        dummyjson_categories: List[str] = []
                        for cat in raw_dummyjson_categories:
                            if isinstance(cat, dict):
                                name = cat.get("category") or cat.get("name")
                                if name:
                                    dummyjson_categories.append(name)
                            else:
                                dummyjson_categories.append(cat)
                        # Combine and dedupe
                        all_categories_set = set(fake_store_categories)
                        all_categories_set.update(dummyjson_categories)
                        # Perform mapping
                        mapping_result = map_user_preference_to_categories(preferences, list(all_categories_set))
                        result = {
                            "preferences": preferences,
                            "available_categories": sorted(list(all_categories_set)),
                            "mapping": mapping_result
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error mapping categories: {str(e)}"
                        )]
                
                elif name == "get_enhanced_products":
                    category = arguments.get("category")
                    limit = arguments.get("limit", 20)
                    search = arguments.get("search")
                    try:
                        async with DummyJSONProductsClient() as client:
                            if search:
                                response = await client.search_products(search)
                                products = response.get('products', [])[:limit]
                            elif category:
                                response = await client.get_products_by_category(category)
                                products = response.get('products', [])[:limit]
                            else:
                                response = await client.get_products(limit=limit)
                                products = response.get('products', [])
                        result = {
                            "source": "DummyJSON Products API",
                            "total_found": len(products),
                            "products": products
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error fetching enhanced products: {str(e)}"
                        )]
                elif name == "get_all_categories":
                    try:
                        async with FakeStoreAPIClient() as fake_store_client:
                            fake_store_categories = await fake_store_client.get_categories()
                        async with DummyJSONProductsClient() as dummyjson_client:
                            raw_dummyjson_categories = await dummyjson_client.get_categories()
                        # Clean dummyjson categories if they are dicts
                        dummyjson_categories: List[str] = []
                        for cat in raw_dummyjson_categories:
                            if isinstance(cat, dict):
                                name = cat.get("category") or cat.get("name")
                                if name:
                                    dummyjson_categories.append(name)
                            else:
                                dummyjson_categories.append(cat)
                        # Combine and dedupe
                        all_categories_set = set(fake_store_categories)
                        all_categories_set.update(dummyjson_categories)
                        result = {
                            "fake_store_categories": fake_store_categories,
                            "dummyjson_categories": dummyjson_categories,
                            "total_categories": len(all_categories_set),
                            "all_unique_categories": list(all_categories_set)
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error fetching categories: {str(e)}"
                        )]
                elif name == "get_upcoming_holidays":
                    country = arguments.get("country", "US")
                    days_ahead = arguments.get("days_ahead", 90)
                    try:
                        async with HolidayAPIClient() as client:
                            holidays = await client.get_next_holidays(country, days_ahead)
                            shopping_suggestions = await client.get_holiday_shopping_suggestions(holidays)
                        result = {
                            "country": country,
                            "upcoming_holidays": holidays,
                            "shopping_suggestions": shopping_suggestions,
                            "total_holidays": len(holidays)
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error fetching holidays: {str(e)}"
                        )]
                elif name == "get_calendar_events":
                    days_ahead = arguments.get("days_ahead", 14)
                    shopping_only = arguments.get("shopping_only", True)
                    try:
                        client = CalendarClient()
                        if shopping_only:
                            events = await client.get_events_needing_shopping(days_ahead)
                        else:
                            events = await client.get_upcoming_events(days_ahead)
                        result = {
                            "events": events,
                            "total_events": len(events),
                            "shopping_events_only": shopping_only,
                            "next_urgent_event": events[0] if events else None
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error fetching calendar events: {str(e)}"
                        )]
                elif name == "get_smart_recommendations":
                    user_id = arguments.get("user_id")
                    include_calendar = arguments.get("include_calendar", True)
                    include_holidays = arguments.get("include_holidays", True)
                    try:
                        async with DummyJSONUsersClient() as user_client:
                            user_preferences = await user_client.get_user_preferences(user_id)
                        recommendations = {
                            "user_id": user_id,
                            "user_profile": user_preferences,
                            "recommendations": []
                        }
                        if include_calendar:
                            calendar_client = CalendarClient()
                            events = await calendar_client.get_events_needing_shopping(14)
                            for event in events[:3]:
                                event_recs = {
                                    "type": "calendar_event",
                                    "event": event['title'],
                                    "urgency": event['shopping_context']['urgency'],
                                    "suggested_categories": event['shopping_context']['suggested_categories'],
                                    "reason": event['shopping_context']['shopping_reason']
                                }
                                recommendations["recommendations"].append(event_recs)
                        if include_holidays:
                            async with HolidayAPIClient() as holiday_client:
                                holidays = await holiday_client.get_next_holidays("US", 30)
                                for holiday in holidays[:2]:
                                    holiday_recs = {
                                        "type": "holiday",
                                        "holiday": holiday['name'],
                                        "days_until": holiday['days_until'],
                                        "suggested_categories": ["gifts", "decorations", "food"],
                                        "reason": f"Prepare for {holiday['name']}"
                                    }
                                    recommendations["recommendations"].append(holiday_recs)
                        async with DummyJSONProductsClient() as product_client:
                            user_categories = user_preferences.get("derived_preferences", {}).get("likely_categories", [])
                            for category in user_categories[:2]:
                                try:
                                    response = await product_client.get_products_by_category(category)
                                    products = response.get('products', [])[:3]
                                    if products:
                                        category_recs = {
                                            "type": "personal_preference",
                                            "category": category,
                                            "products": products,
                                            "reason": f"Based on your interest in {category}"
                                        }
                                        recommendations["recommendations"].append(category_recs)
                                except:
                                    continue
                        return [TextContent(
                            type="text",
                            text=json.dumps(recommendations, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error generating smart recommendations: {str(e)}"
                        )]
                elif name == "normalize_all_data":
                    include_embeddings = arguments.get("include_embeddings", True)
                    try:
                        normalizer = DataNormalizer()
                        # Normalize products
                        logger.info("Normalizing products...")
                        product_collection = await normalizer.normalize_all_products()
                        # Normalize users
                        logger.info("Normalizing users...")
                        user_collection = await normalizer.normalize_all_users()
                        result = {
                            "status": "success",
                            "products": {
                                "total_count": product_collection.total_count,
                                "source_breakdown": getattr(product_collection, 'source_breakdown', None),
                                "category_breakdown": getattr(product_collection, 'category_breakdown', None)
                            },
                            "users": {
                                "total_count": user_collection.total_count,
                                "demographics": getattr(user_collection, 'demographics_breakdown', None)
                            }
                        }
                        # Generate embeddings if requested
                        if include_embeddings:
                            embedding_service = EmbeddingService()
                            # Generate product embeddings
                            product_embeddings = embedding_service.generate_product_embeddings(product_collection.products)
                            embedding_service.save_embeddings(product_embeddings, "products")
                            # Generate user embeddings
                            user_embeddings = embedding_service.generate_user_embeddings(user_collection.users)
                            embedding_service.save_embeddings(user_embeddings, "users")
                            result["embeddings"] = {
                                "products_generated": len(product_embeddings),
                                "users_generated": len(user_embeddings)
                            }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error normalizing data: {str(e)}"
                        )]
                elif name == "generate_embeddings":
                    target = arguments.get("target", "both")
                    try:
                        embedding_service = EmbeddingService()
                        result = {"status": "success", "embeddings_generated": {}}
                        if target in ["products", "both"]:
                            normalizer = DataNormalizer()
                            product_collection = await normalizer.normalize_all_products()
                            product_embeddings = embedding_service.generate_product_embeddings(product_collection.products)
                            embedding_service.save_embeddings(product_embeddings, "products")
                            result["embeddings_generated"]["products"] = len(product_embeddings)
                        if target in ["users", "both"]:
                            normalizer = DataNormalizer()
                            user_collection = await normalizer.normalize_all_users()
                            user_embeddings = embedding_service.generate_user_embeddings(user_collection.users)
                            embedding_service.save_embeddings(user_embeddings, "users")
                            result["embeddings_generated"]["users"] = len(user_embeddings)
                        result["model_info"] = embedding_service.get_model_info()
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error generating embeddings: {str(e)}"
                        )]
                elif name == "semantic_search":
                    # Semantic search with optional category filtering
                    query = arguments.get("query")
                    category = arguments.get("category")
                    top_k = arguments.get("top_k", 5)
                    try:
                        embedding_service = EmbeddingService()
                        embedding_service.load_model()
                        vector_store = ChromaVectorStore()
                        # Generate query embedding
                        query_embedding = embedding_service.model.encode([query])[0]
                        # Build filters
                        filters = {}
                        if category:
                            filters["normalized_category"] = category
                        # Perform vector-based search
                        search_results = vector_store.search_products(
                            query_embedding=query_embedding,
                            n_results=top_k,
                            filters=filters if filters else None
                        )
                        result = {
                            "query": query,
                            "total_embeddings_searched": search_results["total_found"],
                            "results": search_results["products"],
                            "model_info": embedding_service.get_model_info()
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error performing semantic search: {str(e)}"
                        )]
                elif name == "initialize_vector_store":
                    reset_existing = arguments.get("reset_existing", False)
                    try:
                        vector_store = ChromaVectorStore()
                        if reset_existing:
                            vector_store.reset_collections()
                            logger.info("Reset existing collections")
                        # Load normalized data
                        normalizer = DataNormalizer()
                        product_collection = await normalizer.normalize_all_products()
                        user_collection = await normalizer.normalize_all_users()
                        # Load embeddings
                        embedding_service = EmbeddingService()
                        product_embeddings = embedding_service.load_embeddings("products")
                        user_embeddings = embedding_service.load_embeddings("users")
                        if not product_embeddings or not user_embeddings:
                            return [TextContent(
                                type="text",
                                text="Error: Embeddings not found. Run 'generate_embeddings' first."
                            )]
                        # Add to ChromaDB
                        products_added = vector_store.add_products(product_collection.products, product_embeddings)
                        users_added = vector_store.add_users(user_collection.users, user_embeddings)
                        # Get stats
                        stats = vector_store.get_collection_stats()
                        result = {
                            "status": "success",
                            "products_added": products_added,
                            "users_added": users_added,
                            "collection_stats": stats
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error initializing vector store: {str(e)}"
                        )]
                elif name == "rag_search":
                    query = arguments.get("query")
                    user_id = arguments.get("user_id")
                    max_results = arguments.get("max_results", 5)
                    try:
                        context_builder = ContextBuilder()
                        # Build comprehensive context
                        context = await context_builder.build_shopping_context(
                            user_query=query,
                            user_id=user_id,
                            max_products=max_results
                        )
                        # Format for display
                        result = {
                            "query": query,
                            "context_summary": {
                                "products_found": len(context["product_recommendations"]),
                                "user_context_available": bool(context["user_context"]),
                                "calendar_events": len(context["calendar_context"]),
                                "similar_users": len(context["similar_users"])
                            },
                            "recommended_products": context["product_recommendations"],
                            "upcoming_events": context["calendar_context"],
                            "formatted_context": context_builder.format_context_for_llm(context)
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error performing RAG search: {str(e)}"
                        )]
                elif name == "event_shopping_assistant":
                    event_id = arguments.get("event_id")
                    try:
                        context_builder = ContextBuilder()
                        # Build event-specific context
                        context = await context_builder.build_event_shopping_context(event_id)
                        result = {
                            "event_details": context["event"],
                            "shopping_urgency": context["urgency"],
                            "recommended_products": context["product_suggestions"][:8],
                            "shopping_categories": context["shopping_list"]
                        }
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error building event shopping context: {str(e)}"
                        )]
                elif name == "get_vector_store_stats":
                    try:
                        vector_store = ChromaVectorStore()
                        stats = vector_store.get_collection_stats()
                        return [TextContent(
                            type="text",
                            text=json.dumps(stats, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error getting vector store stats: {str(e)}"
                        )]
                elif name == "ai_shopping_assistant":
                    query = arguments.get("query")
                    user_id = arguments.get("user_id")
                    try:
                        ollama_service = OllamaService()
                        # Generate AI-powered cart-aware recommendation
                        recommendation = await ollama_service.generate_cart_aware_recommendation(
                            user_query=query,
                            user_id=user_id
                        )
                        return [TextContent(
                            type="text",
                            text=json.dumps(recommendation, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error generating AI recommendation: {str(e)}"
                        )]
                elif name == "ai_event_planner":
                    event_id = arguments.get("event_id")
                    try:
                        ollama_service = OllamaService()
                        # Generate event-specific shopping advice
                        advice = await ollama_service.generate_event_shopping_advice(event_id)
                        return [TextContent(
                            type="text",
                            text=json.dumps(advice, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error generating event advice: {str(e)}"
                        )]
                elif name == "ai_chat":
                    message = arguments.get("message")
                    conversation_id = arguments.get("conversation_id")
                    user_id = arguments.get("user_id")
                    try:
                        ollama_service = OllamaService()
                        # Handle conversational interaction
                        chat_response = await ollama_service.chat_conversation(
                            message=message,
                            conversation_id=conversation_id,
                            user_id=user_id
                        )
                        return [TextContent(
                            type="text",
                            text=json.dumps(chat_response, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error in AI chat: {str(e)}"
                        )]
                elif name == "get_ai_status":
                    try:
                        ollama_service = OllamaService()
                        status = ollama_service.get_model_status()
                        return [TextContent(
                            type="text",
                            text=json.dumps(status, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error checking AI status: {str(e)}"
                        )]
                
                elif name == "add_to_cart":
                    product_id = arguments.get("product_id")
                    user_id = arguments.get("user_id")
                    quantity = arguments.get("quantity", 1)
                    ai_reasoning = arguments.get("ai_reasoning", "")
                    
                    try:
                        cart_service = self.cart_service
                        result = await cart_service.add_item(
                            user_id=user_id,
                            product_id=product_id,
                            quantity=quantity,
                            ai_reasoning=ai_reasoning
                        )
                        
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error adding to cart: {str(e)}"
                        )]

                elif name == "remove_from_cart":
                    product_id = arguments.get("product_id")
                    user_id = arguments.get("user_id")
                    quantity = arguments.get("quantity")
                    
                    try:
                        cart_service = self.cart_service
                        result = await cart_service.remove_item(
                            user_id=user_id,
                            product_id=product_id,
                            quantity=quantity
                        )
                        
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error removing from cart: {str(e)}"
                        )]

                elif name == "get_cart_contents":
                    user_id = arguments.get("user_id")
                    
                    try:
                        cart_service = self.cart_service
                        result = await cart_service.get_cart_contents(user_id)
                        
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error getting cart contents: {str(e)}"
                        )]

                elif name == "get_cart_suggestions":
                    user_id = arguments.get("user_id")
                    query = arguments.get("query", "")
                    
                    try:
                        cart_service = self.cart_service
                        result = await cart_service.get_smart_suggestions(user_id, query)
                        
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error getting cart suggestions: {str(e)}"
                        )]

                elif name == "clear_cart":
                    user_id = arguments.get("user_id")
                    
                    try:
                        cart_service = self.cart_service
                        result = await cart_service.clear_cart(user_id)
                        
                        return [TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
                    except Exception as e:
                        return [TextContent(
                            type="text",
                            text=f"Error clearing cart: {str(e)}"
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
