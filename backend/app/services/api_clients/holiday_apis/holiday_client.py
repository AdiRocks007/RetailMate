"""
Holiday API Client
Free API for holiday data: https://date.nager.at/api/
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from ..base_client import BaseAPIClient, APIError

logger = logging.getLogger("retailmate-api-holidays")

class HolidayAPIClient(BaseAPIClient):
    """Client for Holiday API - Free holiday data"""
    
    def __init__(self):
        super().__init__(
            base_url="https://date.nager.at/api/v3",
            name="Holiday API",
            rate_limit=100
        )
    
    async def get_public_holidays(self, year: int, country_code: str = "US") -> List[Dict[str, Any]]:
        """Get public holidays for a specific year and country"""
        try:
            response = await self.get(f"/PublicHolidays/{year}/{country_code}")
            logger.info(f"Retrieved {len(response)} holidays for {country_code} {year}")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching holidays: {e}")
            raise
    
    async def get_available_countries(self) -> List[Dict[str, Any]]:
        """Get list of available countries"""
        try:
            response = await self.get("/AvailableCountries")
            logger.info(f"Retrieved {len(response)} available countries")
            return response
            
        except APIError as e:
            logger.error(f"Error fetching countries: {e}")
            raise
    
    async def get_next_holidays(self, country_code: str = "US", days_ahead: int = 90) -> List[Dict[str, Any]]:
        """Get upcoming holidays within specified days"""
        try:
            current_year = datetime.now().year
            holidays = await self.get_public_holidays(current_year, country_code)
            
            # Also get next year's holidays
            next_year_holidays = await self.get_public_holidays(current_year + 1, country_code)
            all_holidays = holidays + next_year_holidays
            
            # Filter for upcoming holidays
            today = date.today()
            upcoming_holidays = []
            
            for holiday in all_holidays:
                holiday_date = datetime.strptime(holiday['date'], '%Y-%m-%d').date()
                days_until = (holiday_date - today).days
                
                if 0 <= days_until <= days_ahead:
                    holiday['days_until'] = days_until
                    upcoming_holidays.append(holiday)
            
            # Sort by date
            upcoming_holidays.sort(key=lambda x: x['days_until'])
            
            logger.info(f"Found {len(upcoming_holidays)} upcoming holidays")
            return upcoming_holidays
            
        except APIError as e:
            logger.error(f"Error fetching next holidays: {e}")
            raise
    
    async def get_holiday_shopping_suggestions(self, holidays: List[Dict]) -> Dict[str, List[str]]:
        """Generate shopping suggestions based on holidays"""
        suggestions = {}
        
        holiday_categories = {
            "Christmas": ["gifts", "decorations", "food", "clothing"],
            "Thanksgiving": ["food", "kitchen", "home"],
            "Halloween": ["costumes", "decorations", "candy"],
            "Valentine's Day": ["gifts", "jewelry", "flowers", "chocolates"],
            "Easter": ["decorations", "food", "gifts", "clothing"],
            "Fourth of July": ["decorations", "food", "outdoor"],
            "New Year's Day": ["party supplies", "food", "clothing"],
            "Mother's Day": ["gifts", "jewelry", "flowers", "beauty"],
            "Father's Day": ["gifts", "tools", "clothing", "electronics"],
            "Memorial Day": ["outdoor", "food", "decorations"],
            "Labor Day": ["outdoor", "food", "clothing"]
        }
        
        for holiday in holidays:
            holiday_name = holiday.get('name', '')
            
            # Try to match holiday names to our categories
            matched_categories = []
            for key, categories in holiday_categories.items():
                if key.lower() in holiday_name.lower():
                    matched_categories = categories
                    break
            
            if not matched_categories:
                # Default suggestions for unmatched holidays
                matched_categories = ["gifts", "food", "decorations"]
            
            suggestions[holiday_name] = {
                "date": holiday.get('date'),
                "days_until": holiday.get('days_until', 0),
                "suggested_categories": matched_categories,
                "shopping_urgency": "high" if holiday.get('days_until', 100) <= 7 else "medium" if holiday.get('days_until', 100) <= 30 else "low"
            }
        
        return suggestions
