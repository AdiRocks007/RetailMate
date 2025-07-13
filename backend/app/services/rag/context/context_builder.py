"""
Context Builder for RetailMate RAG System
Assembles relevant context for LLM queries
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..vector_store.chroma_store import ChromaVectorStore
from ...embeddings.embedding_service import EmbeddingService
from ...api_clients.calendar_apis.calendar_client import CalendarClient
from ...api_clients.holiday_apis.holiday_client import HolidayAPIClient

logger = logging.getLogger("retailmate-context")

class ContextBuilder:
    """Builds context for RAG queries"""
    
    def __init__(self):
        self.vector_store = ChromaVectorStore()
        self.embedding_service = EmbeddingService()
        self.calendar_client = CalendarClient()
        
        logger.info("Context Builder initialized")
    
    async def build_shopping_context(self, user_query: str, user_id: Optional[str] = None, 
                                   max_products: int = 5) -> Dict[str, Any]:
        """Build comprehensive shopping context for a user query"""
        try:
            context = {
                "query": user_query,
                "timestamp": datetime.now().isoformat(),
                "user_context": {},
                "product_recommendations": [],
                "calendar_context": [],
                "similar_users": [],
                "search_metadata": {}
            }
            
            # Generate query embedding
            self.embedding_service.load_model()
            query_embedding = self.embedding_service.model.encode([user_query])[0]
            
            # Get product recommendations based on query
            product_results = self.vector_store.search_products(
                query_embedding=query_embedding,
                n_results=max_products
            )
            context["product_recommendations"] = product_results["products"]
            
            # Add user context if user_id provided
            if user_id:
                try:
                    # Get user's collection info
                    users_collection = self.vector_store.get_or_create_users_collection()
                    user_data = users_collection.get(ids=[user_id], include=["metadatas"])
                    
                    if user_data["ids"]:
                        context["user_context"] = user_data["metadatas"][0]
                        
                        # Find similar users
                        similar_users = self.vector_store.search_similar_users(user_id, n_results=3)
                        context["similar_users"] = similar_users["similar_users"]
                        
                        # Get personalized product recommendations
                        user_categories = context["user_context"].get("preferred_categories", "").split(",")
                        if user_categories and user_categories[0]:  # Check if not empty
                            for category in user_categories[:2]:  # Top 2 categories
                                category_results = self.vector_store.search_products(
                                    query_embedding=query_embedding,
                                    n_results=3,
                                    filters={"category": category.strip()}
                                )
                                if category_results["products"]:
                                    context["product_recommendations"].extend(category_results["products"])
                
                except Exception as e:
                    logger.warning(f"Could not load user context for {user_id}: {e}")
            
            # Get calendar context
            try:
                upcoming_events = await self.calendar_client.get_events_needing_shopping(days_ahead=14)
                context["calendar_context"] = upcoming_events[:3]  # Top 3 urgent events
            except Exception as e:
                logger.warning(f"Could not load calendar context: {e}")
            
            # Remove duplicates from product recommendations
            seen_ids = set()
            unique_products = []
            for product in context["product_recommendations"]:
                if product["id"] not in seen_ids:
                    seen_ids.add(product["id"])
                    unique_products.append(product)
            context["product_recommendations"] = unique_products[:max_products]
            
            # Add search metadata
            context["search_metadata"] = {
                "total_products_found": len(context["product_recommendations"]),
                "user_provided": user_id is not None,
                "calendar_events_found": len(context["calendar_context"]),
                "similar_users_found": len(context["similar_users"])
            }
            
            logger.info(f"Built context with {len(context['product_recommendations'])} products for query: {user_query[:50]}...")
            return context
            
        except Exception as e:
            logger.error(f"Error building shopping context: {e}")
            raise
    
    async def build_event_shopping_context(self, event_id: str) -> Dict[str, Any]:
        """Build context for event-based shopping"""
        try:
            # Get event details
            event_suggestions = await self.calendar_client.get_event_shopping_suggestions(event_id)
            
            context = {
                "event": event_suggestions["event"],
                "shopping_list": event_suggestions["shopping_list"],
                "urgency": event_suggestions["urgency"],
                "product_suggestions": [],
                "context_type": "event_shopping"
            }
            
            # Generate embeddings for shopping list items
            self.embedding_service.load_model()
            shopping_query = " ".join(event_suggestions["shopping_list"])
            query_embedding = self.embedding_service.model.encode([shopping_query])[0]
            
            # Get relevant products
            product_results = self.vector_store.search_products(
                query_embedding=query_embedding,
                n_results=8
            )
            context["product_suggestions"] = product_results["products"]
            
            logger.info(f"Built event shopping context for event: {event_suggestions['event']['title']}")
            return context
            
        except Exception as e:
            logger.error(f"Error building event shopping context: {e}")
            raise
    
    async def build_comparison_context(self, product_ids: List[str]) -> Dict[str, Any]:
        """Build context for product comparison"""
        try:
            context = {
                "comparison_type": "product_comparison",
                "products": [],
                "comparison_factors": []
            }
            
            # Get product details from ChromaDB
            products_collection = self.vector_store.get_or_create_products_collection()
            
            for product_id in product_ids:
                product_data = products_collection.get(
                    ids=[product_id], 
                    include=["metadatas", "documents"]
                )
                
                if product_data["ids"]:
                    product_info = {
                        "id": product_id,
                        "metadata": product_data["metadatas"][0],
                        "description": product_data["documents"][0]
                    }
                    context["products"].append(product_info)
            
            # Determine comparison factors
            if context["products"]:
                factors = set()
                for product in context["products"]:
                    factors.update(product["metadata"].keys())
                context["comparison_factors"] = list(factors)
            
            logger.info(f"Built comparison context for {len(context['products'])} products")
            return context
            
        except Exception as e:
            logger.error(f"Error building comparison context: {e}")
            raise
    
    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context as text for LLM consumption"""
        try:
            formatted_parts = []
            
            # Add query context
            if context.get("query"):
                formatted_parts.append(f"USER QUERY: {context['query']}")
            
            # Add user context
            if context.get("user_context"):
                user = context["user_context"]
                user_info = f"USER PROFILE: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}, "
                user_info += f"Age: {user.get('age', 'unknown')}, Budget: {user.get('budget_range', 'unknown')}, "
                user_info += f"Preferred categories: {user.get('preferred_categories', 'none')}"
                formatted_parts.append(user_info)
            
            # Add calendar context
            if context.get("calendar_context"):
                formatted_parts.append("UPCOMING EVENTS:")
                for event in context["calendar_context"][:3]:
                    event_info = f"- {event['title']} in {event['days_until']} days, "
                    event_info += f"needs: {', '.join(event['shopping_context']['suggested_categories'])}"
                    formatted_parts.append(event_info)
            
            # Add product recommendations
            if context.get("product_recommendations"):
                formatted_parts.append("RELEVANT PRODUCTS:")
                for i, product in enumerate(context["product_recommendations"][:5], 1):
                    product_info = f"{i}. {product['title']} - ${product['price']} "
                    product_info += f"({product['category']}) - {product['similarity']:.2f} relevance"
                    formatted_parts.append(product_info)
            
            # Add similar users insight
            if context.get("similar_users"):
                formatted_parts.append("SIMILAR USERS PREFERENCES:")
                categories = set()
                for user in context["similar_users"]:
                    categories.update(user["preferred_categories"])
                formatted_parts.append(f"Popular categories: {', '.join(list(categories)[:5])}")
            
            return "\n".join(formatted_parts)
            
        except Exception as e:
            logger.error(f"Error formatting context for LLM: {e}")
            return f"Error formatting context: {str(e)}"

    async def get_product_details(self, product_id: str) -> List[Dict]:
        """Get detailed information about a specific product"""
        try:
            # Get product details from ChromaDB by ID
            products_collection = self.vector_store.get_or_create_products_collection()
            product_data = products_collection.get(
                ids=[product_id], 
                include=["metadatas", "documents"]
            )
            
            if product_data["ids"]:
                product_info = {
                    "id": product_id,
                    "metadata": product_data["metadatas"][0],
                    "description": product_data["documents"][0]
                }
                return [product_info]
            
            # If not found by ID, try searching by title/description
            # This is a fallback in case the ID search doesn't work
            return []
            
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return []

    async def search_products(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for products by query"""
        try:
            # Generate query embedding
            self.embedding_service.load_model()
            query_embedding = self.embedding_service.model.encode([query])[0]
            
            # Search products using vector store
            results = self.vector_store.search_products(
                query_embedding=query_embedding,
                n_results=max_results
            )
            
            return results["products"]
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
