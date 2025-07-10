"""
DummyJSON Users API Client
Free API for user data: https://dummyjson.com/users
"""

import logging
from typing import Dict, List, Optional, Any
from ..base_client import BaseAPIClient, APIError

logger = logging.getLogger("retailmate-api-users")

class DummyJSONUsersClient(BaseAPIClient):
    """Client for DummyJSON Users API"""
    
    def __init__(self):
        super().__init__(
            base_url="https://dummyjson.com",
            name="DummyJSON Users",
            rate_limit=100  # Conservative rate limit
        )
    
    async def get_users(self, limit: int = 30, skip: int = 0) -> Dict[str, Any]:
        """Get list of users with pagination"""
        try:
            params = {"limit": limit, "skip": skip}
            response = await self.get("/users", params=params)
            
            logger.info(f"Retrieved {len(response.get('users', []))} users")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching users: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """Get specific user by ID"""
        try:
            response = await self.get(f"/users/{user_id}")
            logger.info(f"Retrieved user: {response.get('firstName', 'Unknown')} {response.get('lastName', '')}")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            raise
    
    async def search_users(self, query: str) -> Dict[str, Any]:
        """Search users by name"""
        try:
            response = await self.get(f"/users/search", params={"q": query})
            logger.info(f"Found {len(response.get('users', []))} users matching '{query}'")
            return response
            
        except APIError as e:
            logger.error(f"Error searching users: {e}")
            raise
    
    async def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Extract shopping preferences from user data"""
        try:
            user_data = await self.get_user_by_id(user_id)
            
            # Extract relevant shopping preferences
            preferences = {
                "demographics": {
                    "age": user_data.get("age"),
                    "gender": user_data.get("gender"),
                    "location": {
                        "city": user_data.get("address", {}).get("city"),
                        "state": user_data.get("address", {}).get("state"),
                        "country": user_data.get("address", {}).get("country")
                    }
                },
                "contact": {
                    "email": user_data.get("email"),
                    "phone": user_data.get("phone")
                },
                "profile": {
                    "firstName": user_data.get("firstName"),
                    "lastName": user_data.get("lastName"),
                    "image": user_data.get("image")
                },
                "derived_preferences": {
                    "likely_categories": self._derive_shopping_categories(user_data),
                    "budget_range": self._estimate_budget_range(user_data),
                    "shopping_style": self._determine_shopping_style(user_data)
                }
            }
            
            return preferences
            
        except APIError as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            raise
    
    def _derive_shopping_categories(self, user_data: Dict) -> List[str]:
        """Derive likely shopping categories from user data"""
        categories = []
        
        age = user_data.get("age", 0)
        gender = user_data.get("gender", "").lower()
        
        # Age-based categories
        if age < 25:
            categories.extend(["electronics", "fashion", "books"])
        elif age < 45:
            categories.extend(["home", "fashion", "electronics", "health"])
        else:
            categories.extend(["home", "health", "books", "garden"])
        
        # Gender-based categories (with awareness this is generalized)
        if gender == "female":
            categories.extend(["beauty", "jewelry", "fashion"])
        elif gender == "male":
            categories.extend(["tools", "automotive", "sports"])
        
        return list(set(categories))  # Remove duplicates
    
    def _estimate_budget_range(self, user_data: Dict) -> str:
        """Estimate budget range from user data"""
        # This is a simplified estimation - in real app, you'd use more sophisticated logic
        age = user_data.get("age", 0)
        
        if age < 25:
            return "budget"  # $0-50
        elif age < 45:
            return "mid-range"  # $50-200
        else:
            return "premium"  # $200+
    
    def _determine_shopping_style(self, user_data: Dict) -> str:
        """Determine shopping style from user data"""
        # Simplified logic based on available data
        return "online"  # Default assumption for digital users
