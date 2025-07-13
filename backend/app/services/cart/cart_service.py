"""
Cart Service for RetailMate
Handles cart operations and AI-powered cart suggestions
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..rag.context.context_builder import ContextBuilder
from ..embeddings.embedding_service import EmbeddingService

logger = logging.getLogger("retailmate-cart")

class CartService:
    """Service for managing shopping carts and AI-powered cart suggestions"""
    # Shared in-memory cart storage across all instances
    _carts: Dict[str, Dict] = {}
    def __init__(self):
        # Use shared cart storage to persist across instances
        self.carts = CartService._carts
        self.context_builder = ContextBuilder()
        self.embedding_service = EmbeddingService()
        logger.info("Cart service initialized")
    
    async def add_item(self, user_id: str, product_id: str, quantity: int = 1, 
                      ai_reasoning: str = "") -> Dict[str, Any]:
        """Add item to cart with AI reasoning"""
        try:
            # Initialize cart if doesn't exist
            if user_id not in self.carts:
                self.carts[user_id] = {
                    "items": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "total_items": 0,
                    "estimated_total": 0.0
                }
            
            # Get product details
            product_context = await self.context_builder.get_product_details(product_id)
            if not product_context:
                raise ValueError(f"Product {product_id} not found")
            
            product = product_context[0]  # First result from context builder
            # Extract fields from metadata
            metadata = product.get("metadata", {})
            title = metadata.get("title")
            price = metadata.get("price")
            category = metadata.get("category")
            if title is None or price is None or category is None:
                raise ValueError(f"Incomplete product data for {product_id}")
            
            # Check if item already in cart
            existing_item = None
            for item in self.carts[user_id]["items"]:
                if item["product_id"] == product_id:
                    existing_item = item
                    break
            
            if existing_item:
                # Update quantity
                existing_item["quantity"] += quantity
                existing_item["updated_at"] = datetime.now().isoformat()
                if ai_reasoning:
                    existing_item["ai_reasoning"] = ai_reasoning
            else:
                # Add new item
                cart_item = {
                    "product_id": product_id,
                    "title": title,
                    "price": price,
                    "category": category,
                    "quantity": quantity,
                    "ai_reasoning": ai_reasoning,
                    "added_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "subtotal": price * quantity
                }
                self.carts[user_id]["items"].append(cart_item)
            
            # Update cart totals
            await self._update_cart_totals(user_id)
            
            logger.info(f"Added {quantity}x {title} to cart for user {user_id}")
            
            return {
                "success": True,
                "message": f"Added {quantity}x {title} to cart",
                "cart_summary": await self.get_cart_summary(user_id),
                "ai_reasoning": ai_reasoning
            }
            
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_item(self, user_id: str, product_id: str, quantity: int = None) -> Dict[str, Any]:
        """Remove item from cart"""
        try:
            if user_id not in self.carts:
                return {"success": False, "error": "Cart not found"}
            
            cart = self.carts[user_id]
            item_found = False
            
            for i, item in enumerate(cart["items"]):
                if item["product_id"] == product_id:
                    if quantity is None or quantity >= item["quantity"]:
                        # Remove entirely
                        removed_item = cart["items"].pop(i)
                        message = f"Removed {removed_item['title']} from cart"
                    else:
                        # Reduce quantity
                        item["quantity"] -= quantity
                        item["subtotal"] = item["price"] * item["quantity"]
                        item["updated_at"] = datetime.now().isoformat()
                        message = f"Reduced {item['title']} quantity by {quantity}"
                    
                    item_found = True
                    break
            
            if not item_found:
                return {"success": False, "error": "Item not found in cart"}
            
            # Update cart totals
            await self._update_cart_totals(user_id)
            
            logger.info(f"Removed item from cart for user {user_id}")
            
            return {
                "success": True,
                "message": message,
                "cart_summary": await self.get_cart_summary(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error removing item from cart: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_cart_contents(self, user_id: str) -> Dict[str, Any]:
        """Get complete cart contents"""
        try:
            if user_id not in self.carts:
                return {
                    "items": [],
                    "total_items": 0,
                    "estimated_total": 0.0,
                    "empty": True
                }
            
            cart = self.carts[user_id]
            
            return {
                "items": cart["items"],
                "total_items": cart["total_items"],
                "estimated_total": cart["estimated_total"],
                "created_at": cart["created_at"],
                "updated_at": cart["updated_at"],
                "empty": len(cart["items"]) == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cart contents: {e}")
            return {"error": str(e)}
    
    async def get_cart_summary(self, user_id: str) -> Dict[str, Any]:
        """Get cart summary for context"""
        try:
            cart_contents = await self.get_cart_contents(user_id)
            
            if cart_contents.get("empty", True):
                return {
                    "empty": True,
                    "total_items": 0,
                    "estimated_total": 0.0
                }
            
            # Category breakdown
            categories = {}
            for item in cart_contents["items"]:
                category = item["category"]
                if category not in categories:
                    categories[category] = {"count": 0, "total": 0.0}
                categories[category]["count"] += item["quantity"]
                categories[category]["total"] += item["subtotal"]
            
            return {
                "empty": False,
                "total_items": cart_contents["total_items"],
                "estimated_total": cart_contents["estimated_total"],
                "categories": categories,
                "recent_additions": [
                    item["title"] for item in cart_contents["items"][-3:]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {"error": str(e)}
    
    async def get_smart_suggestions(self, user_id: str, query: str = "") -> Dict[str, Any]:
        """Get AI-powered cart suggestions"""
        try:
            cart_contents = await self.get_cart_contents(user_id)
            
            if cart_contents.get("empty", True):
                return {
                    "suggestions": {},
                    "message": "Add items to cart to get smart suggestions"
                }
            
            # Build context for suggestions
            cart_context = await self._build_cart_context(user_id)
            
            # Get complementary products
            complementary_products = await self._get_complementary_products(cart_context)
            
            # Get better alternatives
            alternatives = await self._get_better_alternatives(cart_context)
            
            # Get bundle opportunities
            bundles = await self._get_bundle_opportunities(cart_context)
            
            suggestions = {
                "complementary_products": complementary_products,
                "better_alternatives": alternatives,
                "bundle_opportunities": bundles,
                "cart_optimization": await self._analyze_cart_optimization(cart_context)
            }
            
            logger.info(f"Generated {len(complementary_products)} suggestions for user {user_id}")
            
            return {
                "suggestions": suggestions,
                "cart_context": cart_context
            }
            
        except Exception as e:
            logger.error(f"Error getting smart suggestions: {e}")
            return {"error": str(e)}
    
    async def clear_cart(self, user_id: str) -> Dict[str, Any]:
        """Clear user's cart"""
        try:
            if user_id in self.carts:
                del self.carts[user_id]
                logger.info(f"Cleared cart for user {user_id}")
            
            return {
                "success": True,
                "message": "Cart cleared successfully"
            }
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            return {"success": False, "error": str(e)}
    
    async def _update_cart_totals(self, user_id: str):
        """Update cart totals and counts"""
        cart = self.carts[user_id]
        
        total_items = sum(item["quantity"] for item in cart["items"])
        estimated_total = sum(item["subtotal"] for item in cart["items"])
        
        cart["total_items"] = total_items
        cart["estimated_total"] = round(estimated_total, 2)
        cart["updated_at"] = datetime.now().isoformat()
    
    async def _build_cart_context(self, user_id: str) -> Dict[str, Any]:
        """Build comprehensive cart context for AI suggestions"""
        cart_contents = await self.get_cart_contents(user_id)
        
        # Extract categories and price ranges
        categories = set()
        price_ranges = []
        brands = set()
        
        for item in cart_contents["items"]:
            categories.add(item["category"])
            price_ranges.append(item["price"])
            # Extract brand if available
            if "brand" in item:
                brands.add(item["brand"])
        
        return {
            "cart_items": cart_contents["items"],
            "categories": list(categories),
            "price_range": {
                "min": min(price_ranges) if price_ranges else 0,
                "max": max(price_ranges) if price_ranges else 0,
                "avg": sum(price_ranges) / len(price_ranges) if price_ranges else 0
            },
            "brands": list(brands),
            "total_value": cart_contents["estimated_total"]
        }
    
    async def _get_complementary_products(self, cart_context: Dict) -> List[Dict]:
        """Find products that complement cart items"""
        complementary_products = []
        
        for category in cart_context["categories"]:
            # Define complementary relationships
            complementary_map = {
                "electronics": ["laptop bag", "mouse", "keyboard", "charger"],
                "clothing": ["shoes", "accessories", "belt"],
                "kitchen": ["utensils", "storage", "cleaning"],
                "home": ["decor", "lighting", "organization"]
            }
            
            if category in complementary_map:
                for complement in complementary_map[category]:
                    # Search for complementary products
                    search_results = await self.context_builder.search_products(
                        query=complement,
                        max_results=2
                    )
                    
                    for product in search_results:
                        if product["id"] not in [item["product_id"] for item in cart_context["cart_items"]]:
                            complementary_products.append({
                                **product,
                                "suggestion_reason": f"Complements your {category} items",
                                "suggestion_type": "complementary"
                            })
        
        return complementary_products[:5]  # Limit to 5 suggestions
    
    async def _get_better_alternatives(self, cart_context: Dict) -> List[Dict]:
        """Find better alternatives to cart items"""
        alternatives = []
        
        for cart_item in cart_context["cart_items"]:
            # Search for similar products in same category
            similar_products = await self.context_builder.search_products(
                query=cart_item["title"],
                max_results=3
            )
            
            for product in similar_products:
                if (product["id"] != cart_item["product_id"] and 
                    product["category"] == cart_item["category"]):
                    
                    # Check if it's a better deal
                    if product["price"] < cart_item["price"]:
                        alternatives.append({
                            **product,
                            "replaces": cart_item,
                            "savings": cart_item["price"] - product["price"],
                            "suggestion_reason": f"Save ${cart_item['price'] - product['price']:.2f}",
                            "suggestion_type": "better_price"
                        })
                    elif product.get("rating", 0) > cart_item.get("rating", 0):
                        alternatives.append({
                            **product,
                            "replaces": cart_item,
                            "rating_improvement": product.get("rating", 0) - cart_item.get("rating", 0),
                            "suggestion_reason": "Higher rated alternative",
                            "suggestion_type": "better_quality"
                        })
        
        return alternatives[:3]  # Limit to 3 alternatives
    
    async def _get_bundle_opportunities(self, cart_context: Dict) -> List[Dict]:
        """Identify bundle opportunities"""
        bundles = []
        
        # Simple bundle logic - if multiple items from same category
        category_counts = {}
        for item in cart_context["cart_items"]:
            category = item["category"]
            if category not in category_counts:
                category_counts[category] = []
            category_counts[category].append(item)
        
        for category, items in category_counts.items():
            if len(items) >= 2:
                bundle_value = sum(item["price"] * item["quantity"] for item in items)
                potential_savings = bundle_value * 0.1  # 10% bundle discount
                
                bundles.append({
                    "category": category,
                    "items": items,
                    "bundle_value": bundle_value,
                    "potential_savings": potential_savings,
                    "suggestion_reason": f"Bundle {len(items)} {category} items and save 10%",
                    "suggestion_type": "bundle"
                })
        
        return bundles
    
    async def _analyze_cart_optimization(self, cart_context: Dict) -> Dict[str, Any]:
        """Analyze cart for optimization opportunities"""
        optimization = {
            "total_items": len(cart_context["cart_items"]),
            "total_value": cart_context["total_value"],
            "suggestions": []
        }
        
        # Check for shipping optimization
        if cart_context["total_value"] < 50:
            optimization["suggestions"].append({
                "type": "shipping",
                "message": f"Add ${50 - cart_context['total_value']:.2f} more for free shipping",
                "threshold": 50
            })
        
        # Check for quantity discounts
        for item in cart_context["cart_items"]:
            if item["quantity"] == 1 and item["price"] > 20:
                optimization["suggestions"].append({
                    "type": "quantity_discount",
                    "message": f"Buy 2 {item['title']} and save 15%",
                    "item": item
                })
        
        return optimization
