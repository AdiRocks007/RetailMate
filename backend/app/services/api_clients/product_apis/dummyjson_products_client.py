"""
DummyJSON Products API Client
Free API for enhanced product data: https://dummyjson.com/products
"""

import logging
from typing import Dict, List, Optional, Any
from ..base_client import BaseAPIClient, APIError

logger = logging.getLogger("retailmate-api-products")

class DummyJSONProductsClient(BaseAPIClient):
    """Client for DummyJSON Products API - Enhanced product catalog"""
    
    def __init__(self):
        super().__init__(
            base_url="https://dummyjson.com",
            name="DummyJSON Products",
            rate_limit=100
        )
    
    async def get_products(self, limit: int = 30, skip: int = 0) -> Dict[str, Any]:
        """Get products with pagination"""
        try:
            params = {"limit": limit, "skip": skip}
            response = await self.get("/products", params=params)
            
            logger.info(f"Retrieved {len(response.get('products', []))} products from DummyJSON")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching DummyJSON products: {e}")
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
            logger.info(f"Retrieved {len(response)} categories from DummyJSON")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching categories: {e}")
            raise
    
    async def get_products_by_category(self, category: str) -> Dict[str, Any]:
        """Get products in specific category"""
        try:
            response = await self.get(f"/products/category/{category}")
            products = response.get('products', [])
            logger.info(f"Retrieved {len(products)} products in category '{category}'")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching products in category {category}: {e}")
            raise
    
    async def search_products(self, query: str) -> Dict[str, Any]:
        """Search products by title/description"""
        try:
            response = await self.get(f"/products/search", params={"q": query})
            products = response.get('products', [])
            logger.info(f"Found {len(products)} products matching '{query}'")
            return response
            
        except APIError as e:
            logger.error(f"Error searching products: {e}")
            raise
    
    async def get_all_categories_with_products(self) -> Dict[str, List[Dict]]:
        """Get comprehensive category mapping with products"""
        try:
            categories = await self.get_categories()
            category_products = {}
            
            for category in categories:
                try:
                    response = await self.get_products_by_category(category)
                    category_products[category] = response.get('products', [])
                except APIError:
                    category_products[category] = []
            
            logger.info(f"Mapped {len(categories)} categories with products")
            return category_products
            
        except APIError as e:
            logger.error(f"Error mapping categories: {e}")
            raise
