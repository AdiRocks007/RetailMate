"""
Calendar Client with Event Generation
Combines Google Calendar API with generated test events
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import random
from pathlib import Path

logger = logging.getLogger("retailmate-api-calendar")

class CalendarClient:
    """Calendar client with event generation for testing"""
    
    def __init__(self):
        self.name = "Calendar Client"
        self.events_file = Path("backend/app/data/generated/test_events.json")
        self._ensure_events_file_exists()
        
        logger.info("Calendar Client initialized")
    
    def _ensure_events_file_exists(self):
        """Create events file if it doesn't exist"""
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.events_file.exists():
            self.generate_test_events()
    
    def generate_test_events(self, num_events: int = 50) -> List[Dict[str, Any]]:
        """Generate realistic test calendar events"""
        
        event_types = {
            "work": {
                "templates": [
                    "Team Meeting", "Client Presentation", "Project Review", 
                    "Budget Planning", "Training Session", "Conference Call",
                    "Quarterly Review", "Strategy Meeting", "Product Demo"
                ],
                "categories": ["business", "professional", "meeting"],
                "shopping_needs": ["business attire", "notebooks", "tech accessories"]
            },
            "personal": {
                "templates": [
                    "Doctor Appointment", "Gym Session", "Grocery Shopping",
                    "Hair Appointment", "Car Service", "House Cleaning",
                    "Date Night", "Movie Night", "Weekend Getaway"
                ],
                "categories": ["health", "lifestyle", "maintenance"],
                "shopping_needs": ["casual wear", "health products", "home supplies"]
            },
            "social": {
                "templates": [
                    "Birthday Party", "Wedding", "Dinner Party",
                    "Game Night", "Book Club", "BBQ Party",
                    "Concert", "Theater Show", "Art Gallery"
                ],
                "categories": ["celebration", "entertainment", "cultural"],
                "shopping_needs": ["gifts", "party supplies", "formal wear"]
            },
            "family": {
                "templates": [
                    "Family Dinner", "Kids Soccer Game", "School Event",
                    "Family Vacation", "Holiday Celebration", "Anniversary",
                    "Parent-Teacher Conference", "Family Reunion", "Graduation"
                ],
                "categories": ["family", "children", "education"],
                "shopping_needs": ["family gifts", "children's items", "travel gear"]
            },
            "travel": {
                "templates": [
                    "Business Trip", "Weekend Getaway", "Vacation",
                    "Conference Travel", "Family Visit", "Honeymoon",
                    "Road Trip", "International Travel", "Camping Trip"
                ],
                "categories": ["travel", "vacation", "business travel"],
                "shopping_needs": ["luggage", "travel accessories", "clothing"]
            }
        }
        
        events = []
        today = datetime.now()
        
        for i in range(num_events):
            # Random date within next 6 months
            days_ahead = random.randint(1, 180)
            event_date = today + timedelta(days=days_ahead)
            
            # Random event type
            event_type = random.choice(list(event_types.keys()))
            event_data = event_types[event_type]
            
            # Random duration
            duration_hours = random.choice([0.5, 1, 1.5, 2, 3, 4, 8])
            end_date = event_date + timedelta(hours=duration_hours)
            
            event = {
                "id": f"event_{i+1}",
                "title": random.choice(event_data["templates"]),
                "start_date": event_date.isoformat(),
                "end_date": end_date.isoformat(),
                "type": event_type,
                "categories": event_data["categories"],
                "shopping_needs": event_data["shopping_needs"],
                "days_until": days_ahead,
                "attendees": random.randint(1, 10) if event_type in ["social", "work"] else 1,
                "importance": random.choice(["low", "medium", "high"]),
                "preparation_needed": random.choice([True, False]),
                "gift_needed": event_type in ["social", "family"] and random.choice([True, False]),
                "location": random.choice(["Office", "Home", "Restaurant", "Park", "Mall", "Online", "TBD"])
            }
            
            events.append(event)
        
        # Sort events by date
        events.sort(key=lambda x: x['days_until'])
        
        # Save to file
        with open(self.events_file, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated {len(events)} test events")
        return events
    
    async def get_upcoming_events(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming events within specified days"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                all_events = json.load(f)
            
            # Filter for upcoming events
            upcoming_events = [
                event for event in all_events 
                if event['days_until'] <= days_ahead
            ]
            
            logger.info(f"Retrieved {len(upcoming_events)} upcoming events")
            return upcoming_events
            
        except Exception as e:
            logger.error(f"Error loading events: {e}")
            return []
    
    async def get_events_needing_shopping(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """Get events that might need shopping preparation"""
        upcoming_events = await self.get_upcoming_events(days_ahead)
        
        shopping_events = []
        for event in upcoming_events:
            if (event.get('preparation_needed') or 
                event.get('gift_needed') or 
                event['type'] in ['social', 'work', 'travel']):
                
                # Add shopping context
                event['shopping_context'] = {
                    "urgency": "high" if event['days_until'] <= 3 else "medium" if event['days_until'] <= 7 else "low",
                    "suggested_categories": event['shopping_needs'],
                    "budget_range": "high" if event['importance'] == 'high' else "medium",
                    "shopping_reason": self._get_shopping_reason(event)
                }
                shopping_events.append(event)
        
        logger.info(f"Found {len(shopping_events)} events needing shopping")
        return shopping_events
    
    def _get_shopping_reason(self, event: Dict) -> str:
        """Generate shopping reason based on event"""
        if event.get('gift_needed'):
            return f"Gift needed for {event['title']}"
        elif event.get('preparation_needed'):
            return f"Preparation needed for {event['title']}"
        elif event['type'] == 'work':
            return f"Professional attire for {event['title']}"
        elif event['type'] == 'travel':
            return f"Travel essentials for {event['title']}"
        else:
            return f"Items needed for {event['title']}"
    
    async def get_event_shopping_suggestions(self, event_id: str) -> Dict[str, Any]:
        """Get specific shopping suggestions for an event"""
        try:
            with open(self.events_file, 'r', encoding='utf-8') as f:
                all_events = json.load(f)
            
            event = next((e for e in all_events if e['id'] == event_id), None)
            if not event:
                raise ValueError(f"Event {event_id} not found")
            
            suggestions = {
                "event": event,
                "shopping_list": event['shopping_needs'],
                "urgency": "high" if event['days_until'] <= 3 else "medium",
                "budget_estimate": "high" if event['importance'] == 'high' else "medium",
                "shopping_timeline": f"Shop within {min(event['days_until'] - 1, 7)} days"
            }
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting event suggestions: {e}")
            raise
