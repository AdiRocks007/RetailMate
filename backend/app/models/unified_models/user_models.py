"""
Unified User Data Models
Standardizes user data across different APIs
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
from enum import Enum

class GenderType(str, Enum):
    """Gender categories"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class BudgetRange(str, Enum):
    """Budget ranges for shopping"""
    BUDGET = "budget"        # $0-50
    MID_RANGE = "mid-range"  # $50-200
    PREMIUM = "premium"      # $200+

class ShoppingStyle(str, Enum):
    """Shopping style preferences"""
    ONLINE = "online"
    IN_STORE = "in-store"
    HYBRID = "hybrid"

class UserLocation(BaseModel):
    """User location information"""
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State/province")
    country: Optional[str] = Field(None, description="Country")
    timezone: Optional[str] = Field(None, description="User timezone")

class UserContact(BaseModel):
    """User contact information"""
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")

class ShoppingPreferences(BaseModel):
    """User shopping preferences"""
    preferred_categories: List[str] = Field(default_factory=list, description="Preferred product categories")
    budget_range: BudgetRange = Field(default=BudgetRange.MID_RANGE, description="Budget preference")
    shopping_style: ShoppingStyle = Field(default=ShoppingStyle.ONLINE, description="Shopping style")
    favorite_brands: List[str] = Field(default_factory=list, description="Favorite brands")
    avoid_categories: List[str] = Field(default_factory=list, description="Categories to avoid")

class UnifiedUser(BaseModel):
    """Unified user model across all APIs"""
    
    # Core identification
    id: str = Field(description="Unique user identifier")
    source_api: str = Field(description="Source API (dummyjson, github)")
    
    # Basic information
    first_name: str = Field(description="User first name")
    last_name: str = Field(description="User last name")
    username: Optional[str] = Field(None, description="Username")
    
    # Demographics
    age: Optional[int] = Field(None, ge=13, le=120, description="User age")
    gender: Optional[GenderType] = Field(None, description="User gender")
    birth_date: Optional[date] = Field(None, description="Birth date")
    
    # Contact & Location
    contact: Optional[UserContact] = Field(None, description="Contact information")
    location: Optional[UserLocation] = Field(None, description="Location information")
    
    # Profile
    profile_image: Optional[str] = Field(None, description="Profile image URL")
    bio: Optional[str] = Field(None, description="User bio/description")
    
    # Shopping preferences
    shopping_preferences: ShoppingPreferences = Field(default_factory=ShoppingPreferences, description="Shopping preferences")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Record creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Embeddings preparation
    preference_text: str = Field(description="Text representation of user preferences")
    
    @validator('preference_text', pre=True, always=True)
    def generate_preference_text(cls, v, values):
        """Generate text for user preference embeddings"""
        if v:
            return v
        
        parts = []
        
        # Add demographic info
        age = values.get('age')
        if age:
            parts.append(f"age {age}")
        
        gender = values.get('gender')
        if gender:
            parts.append(f"gender {gender}")
        
        # Add location
        location = values.get('location')
        if location and isinstance(location, dict):
            if location.get('city'):
                parts.append(f"from {location['city']}")
            if location.get('country'):
                parts.append(f"country {location['country']}")
        
        # Add shopping preferences
        prefs = values.get('shopping_preferences', {})
        if isinstance(prefs, dict):
            if prefs.get('preferred_categories'):
                parts.append(f"likes {' '.join(prefs['preferred_categories'])}")
            if prefs.get('budget_range'):
                parts.append(f"budget {prefs['budget_range']}")
            if prefs.get('shopping_style'):
                parts.append(f"shops {prefs['shopping_style']}")
        
        return ' '.join(parts) if parts else "general shopper"

class UserCollection(BaseModel):
    """Collection of unified users"""
    users: List[UnifiedUser] = Field(description="List of users")
    total_count: int = Field(description="Total number of users")
    demographics_breakdown: Dict[str, Any] = Field(description="Demographics statistics")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update time")
