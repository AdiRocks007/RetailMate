"""
Ollama Service for RetailMate
Integrates with local Ollama server and Qwen 2.5 model
"""

import logging
import ollama
import json
from typing import Dict, List, Any, Optional
from ...rag.context.context_builder import ContextBuilder
from ...cart.cart_service import CartService
from ..structured_output.response_models import ShoppingAdviceResponse
from pydantic import ValidationError
from ...api_clients.calendar_apis.calendar_client import CalendarClient
from backend.app.services.classify_query import classify_user_query

logger = logging.getLogger("retailmate-ollama")

class OllamaService:
    """Service for interacting with Ollama and Qwen 2.5 model"""
    
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.context_builder = ContextBuilder()
        self.cart_service = CartService()  # Add cart service
        self.conversation_history: Dict[str, List[Dict]] = {}
        # Track last fetched event for follow-up suggestions
        self.last_event_id: Optional[str] = None
        
        logger.info(f"Ollama service initialized with model: {model_name}")
    
    def _verify_model_available(self) -> bool:
        """Verify that the specified model is available"""
        try:
            result = ollama.list()

            # 1) Check raw string output
            if isinstance(result, str):
                if self.model_name in result:
                    logger.info(f"Model {self.model_name} is available (string output)")
                    return True
                logger.warning(f"Model {self.model_name} not found in string output")

            # 2) Normalize API responses
            def extract_models(data) -> List[str]:
                if isinstance(data, dict):
                    return [m.get('name') or m.get('model') for m in data.get('models', []) if isinstance(m, dict)]
                if isinstance(data, list):
                    return [m.get('name') or m.get('model') for m in data if isinstance(m, dict)]
                return []

            available_models = extract_models(result)

            # 🌀 Retry once if list is empty
            if not available_models:
                import time
                logger.warning("No models found on first attempt. Retrying after 2 seconds...")
                time.sleep(2)
                result = ollama.list()
                available_models = extract_models(result)

            if self.model_name in available_models:
                logger.info(f"Model {self.model_name} is available (API output)")
                return True

            logger.warning(f"Model {self.model_name} not found in API output. Models: {available_models}")

            # 3) Fallback: shell out to CLI
            try:
                import subprocess
                proc = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
                output = proc.stdout + proc.stderr
                if self.model_name in output:
                    logger.info(f"Model {self.model_name} is available (CLI fallback)")
                    return True
                logger.warning(f"Model {self.model_name} not found in CLI output")
            except Exception as cli_err:
                logger.error(f"CLI fallback failed: {cli_err}")

            return False

        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def generate_shopping_recommendation(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate shopping recommendations based on user query"""
        try:
            # Build comprehensive context (skip calendar unless explicitly requested)
            context = await self.context_builder.build_shopping_context(
                user_query=user_query,
                user_id=user_id,
                max_products=5
            )
            # Remove calendar events from context for general shopping
            context["calendar_context"] = []
            
            # Format context for LLM
            formatted_context = self.context_builder.format_context_for_llm(context)
            
            # Create shopping-specific prompt
            prompt = self._create_shopping_prompt(user_query, formatted_context)
            
            # Generate free-form response
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are RetailMate, an AI shopping assistant. Provide helpful, personalized shopping recommendations based on the context provided. Be concise but informative."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )
            ai_response = response['message']['content']
            # Separate structured JSON pass (no outlines)
            schema_json = ShoppingAdviceResponse.model_json_schema()
            json_prompt = f"""
Based on your previous advice, convert it into JSON matching this schema:
{schema_json}

Shopping advice:
{ai_response}
"""
            struct_response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are RetailMate, a shopping assistant. Convert free-form advice into JSON matching the provided schema."},
                    {"role": "user", "content": json_prompt},
                ],
                options={"temperature": 0, "top_p": 1.0, "max_tokens": 500},
            )
            structured_content = struct_response['message']['content']
            try:
                structured = ShoppingAdviceResponse.model_validate_json(structured_content)
            except ValidationError:
                # Ignore JSON schema errors silently
                structured = None
            recommendation = {
                "query": user_query,
                "user_id": user_id,
                "ai_response": ai_response,
                "structured_response": structured,
                "context_used": {
                    "products_found": len(context["product_recommendations"]),
                    "calendar_events": len(context["calendar_context"]),
                    "user_context_available": bool(context["user_context"])
                },
                "recommended_products": context["product_recommendations"][:3],
                "model_info": {
                    "model": self.model_name,
                    "tokens_generated": len(ai_response.split())
                }
            }
            
            logger.info(f"Generated recommendation for query: {user_query[:50]}...")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            raise
    
    def _create_shopping_prompt(self, user_query: str, context: str) -> str:
        """Create a shopping-specific prompt for the LLM"""
        prompt = f"""
Based on the following context, help the user with their shopping needs.

USER QUESTION: {user_query}

CONTEXT:
{context}

Please provide:
1. A direct answer to their question
2. Specific product recommendations from the context
3. Why these products are suitable

Keep your response helpful, friendly, and focused on shopping assistance.
"""
        return prompt
    
    async def generate_cart_aware_recommendation(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate cart-aware shopping recommendations"""
        try:
            # Get current cart context
            cart_context = await self.cart_service.get_cart_summary(user_id) if user_id else {}
            
            # Build comprehensive context including cart
            context = await self.context_builder.build_shopping_context(
                user_query=user_query,
                user_id=user_id,
                max_products=5
            )
            
            # Add cart context to the main context
            context["cart_context"] = cart_context
            
            # Format context for LLM
            formatted_context = self.context_builder.format_context_for_llm(context)
            
            # Create cart-aware prompt
            prompt = self._create_cart_aware_prompt(user_query, formatted_context, cart_context)
            
            # Generate response
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": """You are RetailMate, an AI shopping assistant with cart management capabilities. 
                        When recommending products, always consider:
                        1. What's already in the user's cart
                        2. Complementary products that go well together
                        3. Better alternatives if available
                        4. Bundle opportunities for savings
                        5. Cart optimization suggestions
                        
                        Always mention specific actions like "I'll add this to your cart" or "This complements your existing cart items"."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 600
                }
            )
            
            # Extract recommended products and suggest cart actions
            recommended_products = context["product_recommendations"][:3]
            cart_actions = []
            
            # Auto-suggest adding top recommendation to cart
            if recommended_products and user_id:
                top_product = recommended_products[0]
                cart_actions.append({
                    "action": "add_to_cart",
                    "product_id": top_product["id"],
                    "user_id": user_id,
                    "ai_reasoning": f"Based on your query '{user_query}', this product best matches your needs"
                })
            
            recommendation = {
                "query": user_query,
                "user_id": user_id,
                "ai_response": response['message']['content'],
                "cart_context": cart_context,
                "context_used": {
                    "products_found": len(context["product_recommendations"]),
                    "calendar_events": len(context["calendar_context"]),
                    "user_context_available": bool(context["user_context"]),
                    "cart_items": cart_context.get("total_items", 0)
                },
                "recommended_products": recommended_products,
                "suggested_cart_actions": cart_actions,
                "cart_suggestions": await self.cart_service.get_smart_suggestions(user_id) if user_id else {},
                "model_info": {
                    "model": self.model_name,
                    "tokens_generated": len(response['message']['content'].split())
                }
            }
            
            logger.info(f"Generated cart-aware recommendation for query: {user_query[:50]}...")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating cart-aware recommendation: {e}")
            raise

    def _create_cart_aware_prompt(self, user_query: str, context: str, cart_context: Dict) -> str:
        """Create a cart-aware prompt for the LLM"""
        
        cart_info = ""
        if not cart_context.get("empty", True):
            cart_info = f"""
CURRENT CART:
- Total Items: {cart_context.get('total_items', 0)}
- Total Value: ${cart_context.get('estimated_total', 0):.2f}
- Recent Additions: {', '.join(cart_context.get('recent_additions', []))}
- Categories: {', '.join(cart_context.get('categories', {}).keys())}
"""
        else:
            cart_info = "CURRENT CART: Empty"
        
        prompt = f"""
Based on the following context, help the user with their shopping needs while considering their current cart.

USER QUESTION: {user_query}

{cart_info}

CONTEXT:
{context}

Please provide:
1. A direct answer to their question
2. Specific product recommendations from the context
3. How these products work with their current cart
4. Suggestions for cart optimization (bundles, alternatives, complementary items)
5. Any specific actions like "I'll add this to your cart"

Keep your response helpful, friendly, and focused on actionable shopping assistance.
"""
        return prompt
    
    async def generate_event_shopping_advice(self, event_id: str) -> Dict[str, Any]:
        """Generate shopping advice for specific calendar events"""
        try:
            # Build event-specific context
            context = await self.context_builder.build_event_shopping_context(event_id)
            
            # Create event-focused prompt
            event = context["event"]
            prompt = f"""
Help plan shopping for this upcoming event:

EVENT: {event['title']}
DATE: In {event['days_until']} days
TYPE: {event['type']}
URGENCY: {context['urgency']}

SHOPPING NEEDS: {', '.join(context['shopping_list'])}

AVAILABLE PRODUCTS:
{self._format_products_for_prompt(context['product_suggestions'][:5])}

Provide a shopping plan including:
1. Priority items to buy first
2. Budget suggestions
3. Timeline for shopping
4. Specific product recommendations
"""
            
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are RetailMate, an AI shopping assistant specializing in event planning and shopping preparation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.6,
                    "max_tokens": 400
                }
            )
            
            advice = {
                "event_id": event_id,
                "event_title": event['title'],
                "urgency": context['urgency'],
                "ai_advice": response['message']['content'],
                "recommended_products": context['product_suggestions'][:5],
                "shopping_timeline": f"Shop within {event['days_until'] - 1} days"
            }
            
            logger.info(f"Generated event shopping advice for: {event['title']}")
            return advice
            
        except Exception as e:
            logger.error(f"Error generating event advice: {e}")
            raise
    
    def _format_products_for_prompt(self, products: List[Dict]) -> str:
        """Format products for inclusion in prompts"""
        formatted = []
        for i, product in enumerate(products, 1):
            product_text = f"{i}. {product['title']} - ${product['price']} ({product['category']})"
            if product.get('rating'):
                product_text += f" - {product['rating']:.1f}★"
            formatted.append(product_text)
        
        return "\n".join(formatted)
    
    async def chat_conversation(self, message: str, conversation_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Handle conversational chat about shopping, including cart and calendar context"""
        # Initialize conversation history if needed
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        # Build RAG context for shopping
        context = await self.context_builder.build_shopping_context(
            user_query=message,
            user_id=user_id,
            max_products=3
        )
        # Fetch cart summary (use "default" for anonymous sessions)
        cart_summary = await self.cart_service.get_cart_summary(user_id or "default")
        calendar_client = CalendarClient()
        events = await calendar_client.get_upcoming_events()
        # Create conversation prompt including all contexts
        conversation_prompt = self._create_conversation_prompt(
            message,
            self.conversation_history[conversation_id],
            context,
            cart_summary,
            events
        )
        
        # Generate response
        response = ollama.chat(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are RetailMate, a friendly AI shopping assistant. Engage in natural conversation while helping with shopping needs. Keep responses conversational and helpful."
                },
                {
                    "role": "user",
                    "content": conversation_prompt
                }
            ],
            options={
                "temperature": 0.8,
                "max_tokens": 300
            }
        )
        
        # Update conversation history
        self.conversation_history[conversation_id].append({
            "role": "user",
            "content": message
        })
        self.conversation_history[conversation_id].append({
            "role": "assistant",
            "content": response['message']['content']
        })
        
        # Keep only last 10 messages
        if len(self.conversation_history[conversation_id]) > 10:
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-10:]
        
        chat_response = {
            "conversation_id": conversation_id,
            "user_message": message,
            "ai_response": response['message']['content'],
            "context_products": context["product_recommendations"][:2],
            "conversation_length": len(self.conversation_history[conversation_id])
        }
        
        logger.info(f"Generated chat response for conversation: {conversation_id}")
        return chat_response
    
    def _create_conversation_prompt(self, message: str, history: List[Dict], context: Dict, cart_summary: Dict[str, Any], events: List[Dict]) -> str:
        """Create prompt for conversational interaction with history, product, cart, and calendar contexts"""
        # Conversation history
        history_text = ""
        if history:
            for msg in history[-4:]:
                sender = "User" if msg["role"] == "user" else "RetailMate"
                history_text += f"{sender}: {msg['content']}\n"
        # Cart context
        if cart_summary and not cart_summary.get("empty", True):
            cart_text = "CURRENT CART:\n"
            cart_text += f"- Total Items: {cart_summary.get('total_items')}\n"
            cart_text += f"- Estimated Total: ${cart_summary.get('estimated_total')}\n"
            recent = cart_summary.get('recent_additions', [])
            cart_text += f"- Recent Additions: {', '.join(recent)}\n"
        else:
            cart_text = "CURRENT CART: empty\n"
        # Calendar context
        if events:
            events_text = "UPCOMING EVENTS:\n"
            for e in events[:3]:
                events_text += f"- {e['title']} in {e['days_until']} days\n"
        else:
            events_text = "UPCOMING EVENTS: none\n"
        # Product recommendations
        context_text = ""
        if context.get("product_recommendations"):
            context_text = "RELEVANT PRODUCTS:\n"
            for i, product in enumerate(context["product_recommendations"][:3], 1):
                context_text += f"{i}. {product['title']} - ${product['price']}\n"
        # Build final prompt
        prompt = f"""
CONVERSATION HISTORY:
{history_text}
{cart_text}
{events_text}
CURRENT MESSAGE: {message}

{context_text}

Respond naturally, incorporating relevant context (cart items, upcoming events, and product suggestions) to assist the user.
"""
        return prompt
    
    async def interpret_and_act(self, message: str, conversation_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Interpret user message into action and reply using rule-based commands and AI classification."""
        lower_msg = message.strip().lower()
        # Suggest based on last fetched event
        if "suggest" in lower_msg and any(kw in lower_msg for kw in ["that event", "for my next event", "based on my next event", "for that"]):
            if self.last_event_id:
                return {"reply": f"Fetching shopping suggestions for event {self.last_event_id}.", "action": {"type": "suggest_for_event", "event_id": self.last_event_id}}
            return {"reply": "I don't have an event to suggest for. Please ask for your next event first.", "action": {"type": "none"}}
        if "next event" in lower_msg:
            calendar_client = CalendarClient()
            events = await calendar_client.get_upcoming_events()
            if events:
                e = events[0]
                # Remember for follow-up suggestions
                self.last_event_id = e['id']
                return {"reply": f"Your next event is {e['title']} on {e['start_date']} ({e['days_until']} days away).", "action": {"type": "next_event"}}
            # Clear last_event if none
            self.last_event_id = None
            return {"reply": "You have no upcoming events.", "action": {"type": "next_event"}}
        if "calendar" in lower_msg or "upcoming events" in lower_msg:
            return {"reply": "Here are your upcoming events:", "action": {"type": "list_events"}}
        # Inline cart commands
        if lower_msg.startswith("add to cart"):
            parts = message.split()
            if len(parts) >= 4:
                product_id = parts[3]
                quantity = int(parts[4]) if len(parts) >= 5 and parts[4].isdigit() else 1
                return {"reply": f"Adding {quantity}x {product_id} to your cart.", "action": {"type": "add_to_cart", "product_id": product_id, "quantity": quantity}}
            return {"reply": "Usage: add to cart <product_id> [quantity]", "action": {"type": "none"}}
        if lower_msg.startswith("remove from cart"):
            parts = message.split()
            if len(parts) >= 4:
                product_id = parts[3]
                quantity = int(parts[4]) if len(parts) >= 5 and parts[4].isdigit() else None
                return {"reply": f"Removing {quantity or 'all'} of {product_id} from your cart.", "action": {"type": "remove_from_cart", "product_id": product_id, "quantity": quantity}}
            return {"reply": "Usage: remove from cart <product_id> [quantity]", "action": {"type": "none"}}
        if lower_msg in ("show cart", "view cart"):
            return {"reply": "Here is your current cart.", "action": {"type": "show_cart"}}
        if lower_msg.startswith("list events"):
            return {"reply": "Listing your upcoming events.", "action": {"type": "list_events"}}
        if lower_msg.startswith("suggest for event"):
            parts = message.split()
            if len(parts) >= 4:
                event_id = parts[3]
                return {"reply": f"Fetching shopping suggestions for event {event_id}.", "action": {"type": "suggest_for_event", "event_id": event_id}}
            return {"reply": "Usage: suggest for event <event_id>", "action": {"type": "none"}}
        # Generic shopping requests: need/find/search/recommend
        if any(lower_msg.startswith(prefix) for prefix in ("need ", "find ", "search ", "recommend ")):
            return {"reply": f"Searching for \"{message}\"...", "action": {"type": "search", "query": message}}
        # Fallback to AI classification
        classification_str = classify_user_query(message)
        try:
            classification = json.loads(classification_str)
        except Exception:
            classification = {}
        act = classification.get("action")
        # Map classification to actions
        if act in ("recommend", "search", "deal_lookup"):
            return {"reply": f"Searching for \"{message}\"...", "action": {"type": "search", "query": message}}
        if act == "reorder":
            return {"reply": "Which product would you like to reorder? Please specify the product ID.", "action": {"type": "clarify", "clarification": "Please provide a product ID to reorder."}}
        if act in ("assistant_help", "explain"):
            return {"reply": "I can help you shop, manage your cart, and view upcoming events. What can I do for you?", "action": {"type": "none"}}
        # Default fallback: hand off to normal chat_conversation with no initial reply
        return {"action": {"type": "none"}}
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of the Ollama model"""
        try:
            available = self._verify_model_available()
            
            status = {
                "model_name": self.model_name,
                "available": available,
                "active_conversations": len(self.conversation_history),
                "service_status": "ready" if available else "model_unavailable"
            }
            
            if available:
                # Try a simple test
                test_response = ollama.generate(
                    model=self.model_name,
                    prompt="Hello",
                    options={"max_tokens": 5}
                )
                status["test_response"] = test_response.get('response', 'No response')[:50]
                status["service_status"] = "operational"
            
            return status
            
        except Exception as e:
            logger.error(f"Error checking model status: {e}")
            return {
                "model_name": self.model_name,
                "available": False,
                "error": str(e),
                "service_status": "error"
            }
