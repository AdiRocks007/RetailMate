import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime
import json
import requests
import asyncio
import uuid

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import BackendAPI


# Page configuration
st.set_page_config(page_title="RetailMate Chat", layout="wide")

# API Configuration
API_BASE_URL =  "http://127.0.0.1:8000"

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        height: 500px;
        overflow-y: auto;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .system-message {
        background: #f8f9fa;
        color: #6c757d;
        padding: 0.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #dee2e6;
        font-size: 0.9rem;
    }
    
    .product-card {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .action-indicator {
        background: #ffc107;
        color: #212529;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        font-weight: bold;
    }
    
    .quick-action {
        background: linear-gradient(135deg, #2ed573 0%, #17a2b8 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #2ed573;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    .status-indicator.offline {
        background: #dc3545;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .customer-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.8rem 2.2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 180px;
        height: 65px;
        white-space: normal;
        font-size: 1rem;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    }

    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        animation: spin 1s linear infinite;
        display: inline-block;
        margin-right: 10px;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

</style>
""", unsafe_allow_html=True)

# API Client Functions
class RetailMateAPI:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def check_health(self):
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                is_healthy = data.get("status") == "healthy"
                return is_healthy, data
            return False, None
        except Exception as e:
            return False, str(e)

    
    def send_chat_message(self, message, conversation_id=None, user_id=None):
        """Send a chat message to the API"""
        try:
            payload = {
                "message": message,
                "conversation_id": conversation_id,
                "user_id": user_id
            }
            response = requests.post(f"{self.base_url}/chat", json=payload, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def get_shopping_recommendations(self, query, user_id=None):
        """Get shopping recommendations"""
        try:
            payload = {
                "query": query,
                "user_id": user_id
            }
            response = requests.post(f"{self.base_url}/shopping/recommend", json=payload, timeout=30)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def get_cart_contents(self, user_id):
        """Get user's cart contents"""
        try:
            response = requests.get(f"{self.base_url}/cart/{user_id}", timeout=10)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def add_to_cart(self, user_id, product_id, quantity=1):
        """Add item to cart"""
        try:
            payload = {
                "product_id": product_id,
                "quantity": quantity
            }
            response = requests.post(f"{self.base_url}/cart/{user_id}/add", json=payload, timeout=10)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)

# Initialize API client
api_client = RetailMateAPI(API_BASE_URL)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Welcome to RetailMate! I'm your AI assistant ready to help you with any questions about our products and services. How can I assist you today?", "timestamp": datetime.now()}
    ]

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())

if 'user_id' not in st.session_state:
    st.session_state.user_id = "user_123"  # In production, get from authentication

if 'customer_info' not in st.session_state:
    st.session_state.customer_info = {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "membership": "Premium",
        "orders": 23,
        "satisfaction": 4.8
    }

if 'api_status' not in st.session_state:
    st.session_state.api_status = {"healthy": False, "last_check": None}

# Check API health
def check_api_health():
    """Check API health and update session state"""
    healthy, response = api_client.check_health()
    st.session_state.api_status = {
        "healthy": healthy,
        "last_check": datetime.now(),
        "response": response
    }
    return healthy

# Function to display products
def display_products(products, title="Recommended Products"):
    """Display product recommendations"""
    if products:
        st.markdown(f"### 🛍 {title}")
        for product in products:
            st.markdown(f"""
            <div class="product-card">
                <h4>{product.get('name', 'Unknown Product')}</h4>
                <p><strong>Price:</strong> ${product.get('price', 'N/A')}</p>
                <p><strong>Category:</strong> {product.get('category', 'N/A')}</p>
                <p>{product.get('description', 'No description available')}</p>
            </div>
            """, unsafe_allow_html=True)

# Function to send message to API
def send_message_to_api(message):
    """Send message to API and handle response"""
    with st.spinner("🤖 AI is thinking..."):
        success, response = api_client.send_chat_message(
            message, 
            st.session_state.conversation_id, 
            st.session_state.user_id
        )
        
        if success:
            # Update conversation ID if new one was created
            if 'conversation_id' in response:
                st.session_state.conversation_id = response['conversation_id']
            
            # Add AI response to messages
            ai_response = response.get('ai_response', 'I apologize, but I received an empty response.')
            st.session_state.messages.append({
                "role": "assistant", 
                "content": ai_response, 
                "timestamp": datetime.now(),
                "action": response.get('action'),
                "context_products": response.get('context_products', []),
                "recommended_products": response.get('recommended_products', [])
            })
            
            return True, response
        else:
            # Add error message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"I'm sorry, I'm having trouble connecting to my backend services. Error: {response}", 
                "timestamp": datetime.now(),
                "action": None,
                "context_products": [],
                "recommended_products": []
            })
            return False, response

# Check API health on page load
if st.session_state.api_status["last_check"] is None or \
   (datetime.now() - st.session_state.api_status["last_check"]).seconds > 60:
    check_api_health()

# Header with API status
status_class = "status-indicator" if st.session_state.api_status["healthy"] else "status-indicator offline"
status_text = "AI Assistant is Online" if st.session_state.api_status["healthy"] else "AI Assistant is Offline"

st.markdown(f"""
<div class="chat-header">
    <h1>💬 Chat with RetailMate</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem;"><span class="{status_class}"></span>{status_text}</p>
</div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([3, 1])

with col1:
    # Chat interface
    st.markdown("### 💬 Chat Interface")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {message["content"]}<br>
                    <small>{message["timestamp"].strftime("%H:%M")}</small>
                </div>
                """, unsafe_allow_html=True)
            elif message["role"] == "assistant":
                st.markdown(f"""
                <div class="bot-message">
                    <strong>🤖 RetailMate:</strong> {message["content"]}<br>
                    <small>{message["timestamp"].strftime("%H:%M")}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Display action indicator if present
                if message.get("action") and message["action"].get("type") != "none":
                    action_type = message["action"]["type"]
                    st.markdown(f"""
                    <div class="action-indicator">
                        🎯 Action: {action_type.replace('_', ' ').title()}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display products if present
                if message.get("recommended_products"):
                    display_products(message["recommended_products"], "AI Recommendations")
                
                if message.get("context_products"):
                    display_products(message["context_products"], "Related Products")
                    
            else:
                st.markdown(f"""
                <div class="system-message">
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("### ✍ Send Message")
    
    # Quick action buttons
    st.markdown("Quick Actions:")
    
    col1_1, col1_2, col1_3, col1_4 = st.columns(4)
    
    with col1_1:
        if st.button("Product Search"):
            user_message = "I'm looking for product recommendations"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            send_message_to_api(user_message)
            st.rerun()
    
    with col1_2:
        if st.button("Cart Status"):
            user_message = "What's in my cart?"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            send_message_to_api(user_message)
            st.rerun()
    
    with col1_3:
        if st.button("Shopping Help"):
            user_message = "I need help with shopping decisions"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            send_message_to_api(user_message)
            st.rerun()
    
    with col1_4:
        if st.button("Event Planning"):
            user_message = "Help me plan shopping for upcoming events"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            send_message_to_api(user_message)
            st.rerun()
    
    # Text input for custom messages
    user_input = st.text_input("Type your message here...", key="user_input", placeholder="Ask me anything about our products or services!")
    
    if st.button("Send Message") and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": datetime.now()})
        
        # Send to API
        send_message_to_api(user_input)
        st.rerun()

with col2:
    # API Status
    st.markdown("### 🔌 API Status")
    if st.session_state.api_status["healthy"]:
        st.success("✅ Connected to RetailMate API")
        if st.session_state.api_status.get("response"):
            response = st.session_state.api_status["response"]
            st.json({
                "Status": response.get("status", "unknown"),
                "Model": response.get("model_status", "unknown"),
                "Conversations": response.get("active_conversations", 0)
            })
    else:
        st.error("❌ API Connection Failed")
        if st.button("🔄 Retry Connection"):
            check_api_health()
            st.rerun()
    
    # Customer information sidebar
    st.markdown("### 👤 Customer Profile")
    
    st.markdown(f"""
    <div class="customer-info">
        <h4>🌟 {st.session_state.customer_info['name']}</h4>
        <p><strong>Email:</strong> {st.session_state.customer_info['email']}</p>
        <p><strong>Membership:</strong> {st.session_state.customer_info['membership']}</p>
        <p><strong>Total Orders:</strong> {st.session_state.customer_info['orders']}</p>
        <p><strong>Satisfaction:</strong> {st.session_state.customer_info['satisfaction']}/5.0 ⭐</p>
        <p><strong>User ID:</strong> {st.session_state.user_id}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat statistics
    st.markdown("### 📊 Chat Statistics")
    
    total_messages = len([msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]])
    user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
    bot_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
    
    st.metric("Total Messages", total_messages)
    st.metric("Your Messages", user_messages)
    st.metric("AI Responses", bot_messages)
    if st.session_state.conversation_id:
        st.metric("Conversation ID", st.session_state.conversation_id[:8] + "...")
    else:
        st.metric("Conversation ID", "Not started")
  
    # Quick Cart Actions
    st.markdown("### 🛒 Quick Cart Actions")
    
    if st.button("View Cart"):
        with st.spinner("Loading cart..."):
            success, cart_data = api_client.get_cart_contents(st.session_state.user_id)
            if success:
                st.json(cart_data)
            else:
                st.error(f"Failed to load cart: {cart_data}")
    
    # Satisfaction rating
    st.markdown("### ⭐ Rate This Chat")
    rating = st.slider("How satisfied are you with this chat?", 1, 5, 5)
    if st.button("Submit Rating"):
        st.success(f"Thank you for rating this chat {rating}/5 stars!")
    
    # Quick help
    st.markdown("### 🆘 Quick Help")
    st.info("""
    AI Features:
    - Natural language queries
    - Product recommendations
    - Cart management
    - Event-based shopping
    - Conversation memory
    - Smart suggestions
    """)

# Clear chat button
if st.button("🗑 Clear Chat History"):
    st.session_state.messages = [
        {"role": "system", "content": "Chat history cleared. Welcome back to RetailMate! How can I assist you today?", "timestamp": datetime.now()}
    ]
    # Generate new conversation ID
    st.session_state.conversation_id = str(uuid.uuid4())
    st.rerun()

# Chat analytics
st.markdown("### 📈 Chat Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    avg_response_time = "< 2 sec" if st.session_state.api_status["healthy"] else "N/A"
    st.metric("Response Time", avg_response_time, delta="AI-powered")

with col2:
    resolution_rate = "94%" if st.session_state.api_status["healthy"] else "N/A"
    st.metric("Resolution Rate", resolution_rate, delta="2% increase")

with col3:
    satisfaction = "4.8/5" if st.session_state.api_status["healthy"] else "N/A"
    st.metric("AI Satisfaction", satisfaction, delta="0.1 improvement")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>💬 RetailMate AI Chat | Available 24/7 | Powered by Advanced AI</p>
    <p>API Status: {'🟢 Online' if st.session_state.api_status['healthy'] else '🔴 Offline'} | 
    Conversation ID: {st.session_state.conversation_id[:8] + '...' if st.session_state.conversation_id else 'Not started'}</p>
</div>
""", unsafe_allow_html=True)