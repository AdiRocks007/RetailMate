import requests
from typing import Dict, Optional


class BackendAPI:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def check_backend_health(self) -> bool:
        """Check if backend is running and healthy."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except requests.exceptions.RequestException:
            return False

    def get_cart_contents(self, user_id: str) -> Dict:
        """Fetch cart items for a user."""
        try:
            response = requests.get(f"{self.base_url}/cart/{user_id}", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"items": [], "total": 0}
            return {"items": [], "total": 0}
        except requests.exceptions.RequestException:
            return {"items": [], "total": 0}

    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> Dict:
        """Add an item to the user's cart."""
        try:
            payload = {"product_id": product_id, "quantity": quantity}
            response = requests.post(
                f"{self.base_url}/cart/{user_id}/add",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response.json() if response.status_code in [200, 201] else {"success": False}
        except requests.exceptions.RequestException:
            return {"success": False}

    def get_cart_summary(self, user_id: str) -> Dict:
        """Get total items and value in the cart."""
        try:
            response = requests.get(f"{self.base_url}/cart/{user_id}/summary", timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"total_items": 0, "total_value": 0}
            return {"total_items": 0, "total_value": 0}
        except requests.exceptions.RequestException:
            return {"total_items": 0, "total_value": 0}

    def chat_with_ai(self, message: str, user_id: str, conversation_id: Optional[str] = None) -> Dict:
        """Send a message to the AI and get a response."""
        try:
            payload = {
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response.json() if response.status_code == 200 else {"ai_response": "AI unavailable"}
        except requests.exceptions.RequestException:
            return {"ai_response": "Connection error"}

    def get_shopping_recommendations(self, query: str, user_id: str) -> Dict:
        """Get product recommendations based on query."""
        try:
            payload = {"query": query, "user_id": user_id}
            response = requests.post(
                f"{self.base_url}/shopping/recommend",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            return response.json() if response.status_code == 200 else {"recommended_products": []}
        except requests.exceptions.RequestException:
            return {"recommended_products": []}
