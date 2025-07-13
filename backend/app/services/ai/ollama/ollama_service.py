"""
Ollama Service for RetailMate
Integrates with local Ollama server and Qwen 2.5 model
"""

import logging
import ollama
import json
from typing import Dict, List, Any, Optional
from ...rag.context.context_builder import ContextBuilder

logger = logging.getLogger("retailmate-ollama")

class OllamaService:
    """Service for interacting with Ollama and Qwen 2.5 model"""
    
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.context_builder = ContextBuilder()
        self.conversation_history: Dict[str, List[Dict]] = {}
        
        logger.info(f"Ollama service initialized with model: {model_name}")
    
    def _verify_model_available(self) -> bool:
        """Verify that the specified model is available"""
        try:
            models = ollama.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            if self.model_name in available_models:
                logger.info(f"Model {self.model_name} is available")
                return True
            else:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def generate_shopping_recommendation(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate shopping recommendations based on user query"""
        try:
            # Build comprehensive context
            context = await self.context_builder.build_shopping_context(
                user_query=user_query,
                user_id=user_id,
                max_products=5
            )
            
            # Format context for LLM
            formatted_context = self.context_builder.format_context_for_llm(context)
            
            # Create shopping-specific prompt
            prompt = self._create_shopping_prompt(user_query, formatted_context)
            
            # Generate response
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
            
            recommendation = {
                "query": user_query,
                "user_id": user_id,
                "ai_response": response['message']['content'],
                "context_used": {
                    "products_found": len(context["product_recommendations"]),
                    "calendar_events": len(context["calendar_context"]),
                    "user_context_available": bool(context["user_context"])
                },
                "recommended_products": context["product_recommendations"][:3],
                "model_info": {
                    "model": self.model_name,
                    "tokens_generated": len(response['message']['content'].split())
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
4. Any calendar-based suggestions if relevant

Keep your response helpful, friendly, and focused on shopping assistance.
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
        """Handle conversational chat about shopping"""
        try:
            # Initialize conversation history if needed
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            # Build context for the current message
            context = await self.context_builder.build_shopping_context(
                user_query=message,
                user_id=user_id,
                max_products=3
            )
            
            # Create conversation prompt
            conversation_prompt = self._create_conversation_prompt(
                message, 
                self.conversation_history[conversation_id],
                context
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
            
        except Exception as e:
            logger.error(f"Error in chat conversation: {e}")
            raise
    
    def _create_conversation_prompt(self, message: str, history: List[Dict], context: Dict) -> str:
        """Create prompt for conversational interaction"""
        # Format conversation history
        history_text = ""
        if history:
            recent_history = history[-4:]  # Last 4 messages
            for msg in recent_history:
                role = "User" if msg["role"] == "user" else "RetailMate"
                history_text += f"{role}: {msg['content']}\n"
        
        # Format current context
        context_text = ""
        if context["product_recommendations"]:
            context_text = "RELEVANT PRODUCTS:\n"
            for i, product in enumerate(context["product_recommendations"][:3], 1):
                context_text += f"{i}. {product['title']} - ${product['price']}\n"
        
        prompt = f"""
CONVERSATION HISTORY:
{history_text}

CURRENT MESSAGE: {message}

{context_text}

Respond naturally to the user's message, incorporating relevant product information when helpful.
"""
        return prompt
    
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
