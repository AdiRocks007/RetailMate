"""
Fake Store API Client
Free API for product data: https://fakestoreapi.com/
"""

import logging
from typing import Dict, List, Optional, Any
from ..base_client import BaseAPIClient, APIError

logger = logging.getLogger("retailmate-api-products")

class FakeStoreAPIClient(BaseAPIClient):
    """Client for Fake Store API"""
    
    def __init__(self):
        super().__init__(
            base_url="https://fakestoreapi.com",
            name="Fake Store API",
            rate_limit=1000  # No explicit rate limit, but being conservative
        )
    
    async def get_products(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all products or limited number"""
        try:
            endpoint = "/products"
            params = {"limit": limit} if limit else None
            
            response = await self.get(endpoint, params=params)
            
            logger.info(f"Retrieved {len(response)} products")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching products: {e}")
            raise
    
    async def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Get specific product by ID"""
        try:
            response = await self.get(f"/products/{product_id}")
            logger.info(f"Retrieved product: {response.get('title', 'Unknown')}")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching product {product_id}: {e}")
            raise
    
    async def get_categories(self) -> List[str]:
        """Get all product categories"""
        try:
            response = await self.get("/products/categories")
            logger.info(f"Retrieved {len(response)} categories")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching categories: {e}")
            raise
    
    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products in specific category"""
        try:
            response = await self.get(f"/products/category/{category}")
            logger.info(f"Retrieved {len(response)} products in category '{category}'")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching products in category {category}: {e}")
            raise
    
    async def search_products(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search products by title/description"""
        try:
            # Get all products (or by category)
            if category:
                products = await self.get_products_by_category(category)
            else:
                products = await self.get_products()
            
            # Simple text search
            query_lower = query.lower()
            filtered_products = []
            
            for product in products:
                title = product.get("title", "").lower()
                description = product.get("description", "").lower()
                
                if query_lower in title or query_lower in description:
                    filtered_products.append(product)
            
            logger.info(f"Found {len(filtered_products)} products matching '{query}'")
            return filtered_products
            
        except APIError as e:
            logger.error(f"Error searching products: {e}")
            raise
    
    async def get_product_recommendations(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get product recommendations based on user preferences"""
        try:
            recommendations = []
            
            # Get user's preferred categories
            preferred_categories = user_preferences.get("derived_preferences", {}).get("likely_categories", [])
            budget_range = user_preferences.get("derived_preferences", {}).get("budget_range", "mid-range")
            
            # Map budget ranges to price ranges
            price_ranges = {
                "budget": (0, 50),
                "mid-range": (50, 200),
                "premium": (200, float('inf'))
            }
            
            min_price, max_price = price_ranges.get(budget_range, (0, float('inf')))
            
            # Get products from preferred categories
            for category in preferred_categories:
                try:
                    category_products = await self.get_products_by_category(category)
                    
                    # Filter by price range
                    for product in category_products:
                        price = product.get("price", 0)
                        if min_price <= price <= max_price:
                            product["recommendation_reason"] = f"Matches your interest in {category} within budget"
                            recommendations.append(product)
                            
                except APIError:
                    continue  # Skip categories that don't exist
            
            # If no category matches, get general recommendations
            if not recommendations:
                all_products = await self.get_products(limit=10)
                for product in all_products:
                    price = product.get("price", 0)
                    if min_price <= price <= max_price:
                        product["recommendation_reason"] = "Popular item within your budget"
                        recommendations.append(product)
            
            logger.info(f"Generated {len(recommendations)} product recommendations")
            return recommendations[:10]  # Limit to top 10
            
        except APIError as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
