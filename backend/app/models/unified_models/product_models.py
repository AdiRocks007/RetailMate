"""
Unified Product Data Models
Standardizes product data across different APIs
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class ProductCategory(str, Enum):
    """Standardized product categories"""
    BEAUTY = "beauty"
    ELECTRONICS = "electronics"
    CLOTHING_MENS = "mens-clothing"
    CLOTHING_WOMENS = "womens-clothing"
    JEWELRY = "jewelry"
    HOME = "home"
    FURNITURE = "furniture"
    GROCERIES = "groceries"
    KITCHEN = "kitchen"
    SPORTS = "sports"
    AUTOMOTIVE = "automotive"
    BOOKS = "books"
    TOYS = "toys"
    HEALTH = "health"

class ProductRating(BaseModel):
    """Product rating information"""
    average: float = Field(ge=0, le=5, description="Average rating 0-5")
    count: int = Field(ge=0, description="Number of reviews")
    source: str = Field(description="Source of rating data")

class ProductDimensions(BaseModel):
    """Product physical dimensions"""
    width: Optional[float] = Field(None, ge=0, description="Width in cm")
    height: Optional[float] = Field(None, ge=0, description="Height in cm")
    depth: Optional[float] = Field(None, ge=0, description="Depth in cm")
    weight: Optional[float] = Field(None, ge=0, description="Weight in grams")

class ProductReview(BaseModel):
    """Individual product review"""
    reviewer_name: str = Field(description="Name of reviewer")
    rating: int = Field(ge=1, le=5, description="Rating 1-5")
    comment: str = Field(description="Review comment")
    date: datetime = Field(description="Review date")
    verified: bool = Field(default=False, description="Verified purchase")

class ProductAvailability(BaseModel):
    """Product availability information"""
    in_stock: bool = Field(description="Whether product is in stock")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    availability_status: str = Field(description="Availability status text")

class UnifiedProduct(BaseModel):
    """Unified product model across all APIs"""
    
    # Core identification
    id: str = Field(description="Unique product identifier")
    source_api: str = Field(description="Source API (fake_store, dummyjson)")
    
    # Basic information
    title: str = Field(description="Product title")
    description: str = Field(description="Product description")
    category: str = Field(description="Product category")
    normalized_category: ProductCategory = Field(description="Standardized category")
    
    # Pricing
    price: float = Field(ge=0, description="Product price")
    currency: str = Field(default="USD", description="Price currency")
    discount_percentage: Optional[float] = Field(None, ge=0, le=100, description="Discount percentage")
    original_price: Optional[float] = Field(None, ge=0, description="Original price before discount")
    
    # Media
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    thumbnail: Optional[str] = Field(None, description="Thumbnail image URL")
    
    # Product details
    brand: Optional[str] = Field(None, description="Product brand")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    
    # Quality indicators
    rating: Optional[ProductRating] = Field(None, description="Product rating")
    reviews: List[ProductReview] = Field(default_factory=list, description="Product reviews")
    
    # Physical properties
    dimensions: Optional[ProductDimensions] = Field(None, description="Product dimensions")
    
    # Availability
    availability: Optional[ProductAvailability] = Field(None, description="Availability info")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    
    # Search optimization
    search_keywords: List[str] = Field(default_factory=list, description="Generated search keywords")
    embedding_text: str = Field(description="Text for embedding generation")
    
    @validator('normalized_category', pre=True)
    def normalize_category(cls, v, values):
        """Normalize category to standard enum"""
        category = values.get('category', '').lower()
        
        # Category mapping
        category_map = {
            "beauty": ProductCategory.BEAUTY,
            "electronics": ProductCategory.ELECTRONICS,
            "men's clothing": ProductCategory.CLOTHING_MENS,
            "mens-clothing": ProductCategory.CLOTHING_MENS,
            "women's clothing": ProductCategory.CLOTHING_WOMENS,
            "womens-clothing": ProductCategory.CLOTHING_WOMENS,
            "jewelery": ProductCategory.JEWELRY,
            "jewelry": ProductCategory.JEWELRY,
            "home-decoration": ProductCategory.HOME,
            "furniture": ProductCategory.FURNITURE,
            "groceries": ProductCategory.GROCERIES,
            "kitchen-accessories": ProductCategory.KITCHEN,
            "sports-accessories": ProductCategory.SPORTS,
        }
        
        return category_map.get(category, ProductCategory.ELECTRONICS)
    
    @validator('embedding_text', pre=True, always=True)
    def generate_embedding_text(cls, v, values):
        """Generate text for embedding"""
        if v:
            return v
        
        parts = [
            values.get('title', ''),
            values.get('description', ''),
            values.get('category', ''),
            values.get('brand', ''),
            ' '.join(values.get('tags', []))
        ]
        
        return ' '.join(filter(None, parts))
    
    @validator('search_keywords', pre=True, always=True)
    def generate_search_keywords(cls, v, values):
        """Generate search keywords"""
        if v:
            return v
        
        keywords = set()
        
        # Add title words
        title = values.get('title', '')
        keywords.update(title.lower().split())
        
        # Add category
        category = values.get('category', '')
        keywords.add(category.lower())
        
        # Add brand
        brand = values.get('brand', '')
        if brand:
            keywords.add(brand.lower())
        
        # Add tags
        tags = values.get('tags', [])
        keywords.update([tag.lower() for tag in tags])
        
        return list(keywords)

class ProductCollection(BaseModel):
    """Collection of unified products"""
    products: List[UnifiedProduct] = Field(description="List of products")
    total_count: int = Field(description="Total number of products")
    source_breakdown: Dict[str, int] = Field(description="Count by source API")
    category_breakdown: Dict[str, int] = Field(description="Count by category")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
