"""
Structured Output Models for RetailMate AI Responses
Uses Outlines for guaranteed JSON structure
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class RecommendationReason(str, Enum):
    """Reasons for product recommendations"""
    PRICE_MATCH = "price_match"
    CATEGORY_PREFERENCE = "category_preference"
    HIGH_RATING = "high_rating"
    CALENDAR_EVENT = "calendar_event"
    SIMILAR_USERS = "similar_users"
    SEMANTIC_MATCH = "semantic_match"

class ShoppingUrgency(str, Enum):
    """Shopping urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ProductRecommendation(BaseModel):
    """Individual product recommendation"""
    product_id: str = Field(description="Product identifier")
    title: str = Field(description="Product title")
    price: float = Field(description="Product price")
    category: str = Field(description="Product category")
    recommendation_reason: RecommendationReason = Field(description="Why this product is recommended")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation")
    brief_explanation: str = Field(description="Brief explanation of why this product fits")

class ShoppingAdviceResponse(BaseModel):
    """Structured shopping advice response"""
    user_query: str = Field(description="Original user query")
    main_advice: str = Field(description="Primary shopping advice")
    recommended_products: List[ProductRecommendation] = Field(description="Product recommendations")
    budget_estimate: Optional[str] = Field(None, description="Estimated budget range")
    shopping_urgency: ShoppingUrgency = Field(description="How urgent this shopping is")
    additional_tips: List[str] = Field(default_factory=list, description="Additional shopping tips")

class EventShoppingPlan(BaseModel):
    """Structured event shopping plan"""
    event_title: str = Field(description="Event name")
    days_until_event: int = Field(description="Days until the event")
    shopping_urgency: ShoppingUrgency = Field(description="Urgency level")
    priority_items: List[str] = Field(description="Items to buy first")
    recommended_products: List[ProductRecommendation] = Field(description="Specific product recommendations")
    shopping_timeline: str = Field(description="When to shop for different items")
    budget_breakdown: Dict[str, float] = Field(description="Budget allocation by category")

class ConversationResponse(BaseModel):
    """Structured conversation response"""
    response_text: str = Field(description="Natural language response")
    intent_detected: str = Field(description="Detected user intent")
    products_mentioned: List[ProductRecommendation] = Field(default_factory=list, description="Products referenced")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    action_suggested: Optional[str] = Field(None, description="Suggested next action")
