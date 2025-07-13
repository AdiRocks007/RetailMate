#!/usr/bin/env python3
"""
FastAPI Backend Server for RetailMate
Exposes OllamaService and CartService as REST APIs
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, BaseSettings
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import logging
import os
from contextlib import asynccontextmanager

# Import your existing services
from backend.app.services.ai.ollama.ollama_service import OllamaService
from backend.app.services.cart.cart_service import CartService
from backend.app.services.api_clients.calendar_apis.calendar_client import CalendarClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retailmate-api")

# Settings configuration
class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    environment: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Initialize services (will be properly initialized in lifespan)
ollama_service = None
cart_service = None
calendar_client = None

# In-memory storage for conversation sessions
# TODO: Replace with Redis or database for production
conversation_sessions = {}

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global ollama_service, cart_service, calendar_client
    logger.info("Starting RetailMate API...")
    
    try:
        ollama_service = OllamaService()
        cart_service = CartService()
        calendar_client = CalendarClient()
        
        # Initialize services if they have async init methods
        # await ollama_service.initialize() # if exists
        # await cart_service.initialize() # if exists
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down RetailMate API...")
    # Add cleanup code here if needed

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="RetailMate API",
    description="AI-powered shopping assistant backend",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "message": "I need ingredients for pasta",
                "user_id": "user123"
            }
        }

class ChatResponse(BaseModel):
    conversation_id: str
    ai_response: str
    action: Optional[Dict[str, Any]] = None
    context_products: Optional[List[Dict[str, Any]]] = None
    recommended_products: Optional[List[Dict[str, Any]]] = None

class ShoppingRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "healthy breakfast options",
                "user_id": "user123"
            }
        }

class CartActionRequest(BaseModel):
    product_id: str
    quantity: int = 1
    user_id: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "product_id": "prod123",
                "quantity": 2
            }
        }

class EventRequest(BaseModel):
    event_id: str

# Helper functions
def get_conversation_id(request_id: Optional[str] = None) -> str:
    """Get or create conversation ID with better validation"""
    if request_id:
        # Validate UUID format
        try:
            uuid.UUID(request_id)
            if request_id in conversation_sessions:
                return request_id
        except ValueError:
            logger.warning(f"Invalid conversation ID format: {request_id}")
    
    new_id = str(uuid.uuid4())
    conversation_sessions[new_id] = {
        "created_at": asyncio.get_event_loop().time(),
        "messages": []
    }
    return new_id

def validate_user_id(user_id: Optional[str]) -> str:
    """Validate and return user ID"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    if len(user_id) < 1 or len(user_id) > 100:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    return user_id

def validate_event_id(event_id: str) -> str:
    """Validate event ID"""
    if not event_id or len(event_id) < 1:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    return event_id

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RetailMate API is running",
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check if services are initialized
        if not ollama_service or not cart_service or not calendar_client:
            return {"status": "unhealthy", "error": "Services not initialized"}
            
        model_status = ollama_service.get_model_status()
        return {
            "status": "healthy",
            "model_status": model_status,
            "active_conversations": len(conversation_sessions),
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint that handles user messages intelligently"""
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service not available")
            
        # Validate message
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get or create conversation ID
        conversation_id = get_conversation_id(request.conversation_id)
        
        # Use the interpret_and_act method for intelligent routing
        interpretation = await ollama_service.interpret_and_act(
            request.message, 
            conversation_id, 
            request.user_id
        )
        
        # Handle different action types
        action = interpretation.get("action", {})
        action_type = action.get("type")
        
        ai_response = interpretation.get("reply", "")
        context_products = []
        recommended_products = []
        
        # Execute actions based on interpretation
        if action_type == "search":
            search_result = await ollama_service.generate_shopping_recommendation(
                action.get("query", request.message),
                request.user_id
            )
            ai_response = search_result.get("ai_response", ai_response)
            recommended_products = search_result.get("recommended_products", [])
            
        elif action_type == "none":
            chat_result = await ollama_service.chat_conversation(
                request.message,
                conversation_id,
                request.user_id
            )
            ai_response = chat_result.get("ai_response", ai_response)
            context_products = chat_result.get("context_products", [])
            
        elif action_type == "suggest_for_event":
            event_advice = await ollama_service.generate_event_shopping_advice(
                action.get("event_id")
            )
            ai_response = event_advice.get("ai_response", ai_response)
            recommended_products = event_advice.get("recommended_products", [])
        
        # Store conversation in session
        if conversation_id in conversation_sessions:
            conversation_sessions[conversation_id]["messages"].append({
                "user": request.message,
                "ai": ai_response,
                "timestamp": asyncio.get_event_loop().time()
            })
        
        return ChatResponse(
            conversation_id=conversation_id,
            ai_response=ai_response,
            action=action,
            context_products=context_products,
            recommended_products=recommended_products
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shopping/recommend")
async def shopping_recommend(request: ShoppingRequest):
    """Generate shopping recommendations"""
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service not available")
            
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        result = await ollama_service.generate_shopping_recommendation(
            request.query,
            request.user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shopping recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/shopping/cart-aware")
async def cart_aware_shopping(request: ShoppingRequest):
    """Generate cart-aware shopping recommendations"""
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service not available")
            
        validated_user_id = validate_user_id(request.user_id)
        
        result = await ollama_service.generate_cart_aware_recommendation(
            request.query,
            validated_user_id
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cart-aware shopping error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/events/{event_id}/shopping-advice")
async def event_shopping_advice(event_id: str):
    """Generate shopping advice for a specific event"""
    try:
        if not ollama_service:
            raise HTTPException(status_code=503, detail="Ollama service not available")
            
        validated_event_id = validate_event_id(event_id)
        result = await ollama_service.generate_event_shopping_advice(validated_event_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Event shopping advice error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Cart Management Endpoints

@app.get("/cart/{user_id}")
async def get_cart(user_id: str):
    """Get user's cart contents"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        cart = await cart_service.get_cart_contents(validated_user_id)
        return cart
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cart error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cart/{user_id}/summary")
async def get_cart_summary(user_id: str):
    """Get user's cart summary"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        summary = await cart_service.get_cart_summary(validated_user_id)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cart summary error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/cart/{user_id}/add")
async def add_to_cart(user_id: str, request: CartActionRequest):
    """Add item to cart"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
            
        result = await cart_service.add_item(
            validated_user_id,
            request.product_id,
            request.quantity
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/cart/{user_id}/remove")
async def remove_from_cart(user_id: str, request: CartActionRequest):
    """Remove item from cart"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        
        result = await cart_service.remove_item(
            validated_user_id,
            request.product_id,
            request.quantity if request.quantity > 0 else None
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove from cart error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/cart/{user_id}/clear")
async def clear_cart(user_id: str):
    """Clear user's cart"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        result = await cart_service.clear_cart(validated_user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear cart error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cart/{user_id}/suggestions")
async def get_cart_suggestions(user_id: str):
    """Get smart cart suggestions"""
    try:
        if not cart_service:
            raise HTTPException(status_code=503, detail="Cart service not available")
            
        validated_user_id = validate_user_id(user_id)
        suggestions = await cart_service.get_smart_suggestions(validated_user_id)
        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cart suggestions error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Calendar Endpoints

@app.get("/calendar/events")
async def get_upcoming_events():
    """Get upcoming calendar events"""
    try:
        if not calendar_client:
            raise HTTPException(status_code=503, detail="Calendar service not available")
            
        events = await calendar_client.get_upcoming_events()
        return {"events": events}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get events error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/calendar/events/{event_id}")
async def get_event_details(event_id: str):
    """Get details for a specific event"""
    try:
        if not calendar_client:
            raise HTTPException(status_code=503, detail="Calendar service not available")
            
        validated_event_id = validate_event_id(event_id)
        events = await calendar_client.get_upcoming_events()
        event = next((e for e in events if e["id"] == validated_event_id), None)
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
            
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get event details error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Session Management

@app.get("/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get conversation history"""
    try:
        uuid.UUID(conversation_id)  # Validate UUID format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
    if conversation_id not in conversation_sessions:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation_sessions[conversation_id]

@app.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    try:
        uuid.UUID(conversation_id)  # Validate UUID format
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")
        
    if conversation_id in conversation_sessions:
        del conversation_sessions[conversation_id]
        return {"message": "Conversation cleared"}
    raise HTTPException(status_code=404, detail="Conversation not found")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info"
    )