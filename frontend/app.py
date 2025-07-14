import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import warnings
import requests
import json
from typing import Dict, List, Optional

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import BackendAPI

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(
    page_title="RetailMate - Smart Retail Management",
    page_icon="🛍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration
API_BASE_URL =  "http://127.0.0.1:8000"
API_TIMEOUT = 10

# ADD THIS DEBUG CODE HERE:
st.markdown("### 🔍 Enhanced Backend Connection Debug")
try:
    # Test with longer timeout
    response = requests.get(f"{API_BASE_URL}/health", timeout=10)
    st.success(f"✅ Backend connected! Status: {response.status_code}")
    st.json(response.json())
    
    # Test specific endpoint
    health_data = response.json()
    model_status = health_data.get("model_status", {})
    st.info(f"Model: {model_status.get('model_name', 'Unknown')}")
    st.info(f"Model Available: {model_status.get('available', False)}")
    
except requests.exceptions.Timeout:
    st.error("❌ Connection timeout - Backend is running but not responding within 10 seconds")
except requests.exceptions.ConnectionError:
    st.error("❌ Connection refused - Backend is not running or not accessible")
except Exception as e:
    st.error(f"❌ Other error: {e}")

# Continue with your existing code...

# Initialize session state
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user_123"
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None
if 'backend_connected' not in st.session_state:
    st.session_state.backend_connected = False

# Backend API Functions
class BackendAPI:
    @staticmethod
    def check_backend_health():
        """Check if backend is running"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except requests.exceptions.RequestException as e:
            st.error(f"Backend connection failed: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return False

    @staticmethod
    def get_cart_contents(user_id: str) -> Dict:
        """Get cart contents from backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/cart/{user_id}", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"items": [], "total": 0}
            else:
                st.warning(f"Cart API returned status {response.status_code}")
                return {"items": [], "total": 0}
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching cart: {str(e)}")
            return {"items": [], "total": 0}
    
    @staticmethod
    def add_to_cart(user_id: str, product_id: str, quantity: int = 1) -> Dict:
        """Add item to cart via backend"""
        try:
            payload = {
                "product_id": product_id,
                "quantity": quantity
            }
            response = requests.post(
                f"{API_BASE_URL}/cart/{user_id}/add",
                json=payload,
                timeout=API_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                st.error(f"Add to cart failed: {response.status_code}")
                return {"success": False}
        except requests.exceptions.RequestException as e:
            st.error(f"Error adding to cart: {str(e)}")
            return {"success": False}
    
    @staticmethod
    def get_cart_summary(user_id: str) -> Dict:
        """Get cart summary from backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/cart/{user_id}/summary", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"total_items": 0, "total_value": 0}
            else:
                return {"total_items": 0, "total_value": 0}
        except requests.exceptions.RequestException:
            return {"total_items": 0, "total_value": 0}
    
    @staticmethod
    def chat_with_ai(message: str, user_id: str, conversation_id: str = None) -> Dict:
        """Chat with AI backend"""
        try:
            payload = {
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id
            }
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=payload,
                timeout=API_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"ai_response": "Sorry, I'm having trouble connecting."}
        except requests.exceptions.RequestException as e:
            st.error(f"Error chatting with AI: {str(e)}")
            return {"ai_response": "Sorry, I'm having trouble connecting."}
    
    @staticmethod
    def get_shopping_recommendations(query: str, user_id: str) -> Dict:
        """Get shopping recommendations from backend"""
        try:
            payload = {
                "query": query,
                "user_id": user_id
            }
            response = requests.post(
                f"{API_BASE_URL}/shopping/recommend",
                json=payload,
                timeout=API_TIMEOUT,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"recommended_products": []}
        except requests.exceptions.RequestException as e:
            st.error(f"Error getting recommendations: {str(e)}")
            return {"recommended_products": []}

# Check backend connection with detailed feedback
st.markdown("### 🔍 Backend Connection Test")
api = BackendAPI()

# Test backend connection
with st.spinner("Testing backend connection..."):
    try:
        test_response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if test_response.status_code == 200:
            st.success(f"✅ Backend connected successfully! Response: {test_response.json()}")
            st.session_state.backend_connected = True
        else:
            st.error(f"❌ Backend returned status {test_response.status_code}")
            st.session_state.backend_connected = False
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Connection refused to {API_BASE_URL}. Is your backend running?")
        st.session_state.backend_connected = False
    except requests.exceptions.Timeout:
        st.error(f"❌ Connection timeout to {API_BASE_URL}")
        st.session_state.backend_connected = False
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.session_state.backend_connected = False

# Show backend status
if st.session_state.backend_connected:
    st.info("🟢 Backend is running and connected")
else:
    st.warning("🔴 Backend is not connected. Some features will be limited.")
    st.markdown("""
    **To fix this:**
    1. Make sure your FastAPI backend is running on `http://localhost:8000`
    2. Check that the backend has a `/health` endpoint
    3. Verify CORS is configured properly
    4. Try running: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
    """)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .feature-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .cart-notification {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
    }
    
    .product-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border: 2px solid #f0f0f0;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .backend-status {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .status-connected {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-disconnected {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### 🛍 RetailMate")

# Backend connection status in sidebar
if st.session_state.backend_connected:
    st.sidebar.markdown("""
    <div class="backend-status status-connected">
        ✅ Backend Connected
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div class="backend-status status-disconnected">
        ❌ Backend Disconnected
    </div>
    """, unsafe_allow_html=True)

# Get cart summary
if st.session_state.backend_connected:
    cart_summary = api.get_cart_summary(st.session_state.user_id)
    total_cart_items = cart_summary.get("total_items", 0)
    total_cart_value = cart_summary.get("total_value", 0)
else:
    total_cart_items = len(st.session_state.cart_items)
    total_cart_value = sum(item.get('price', 0) * item.get('quantity', 1) for item in st.session_state.cart_items)

# Cart summary in sidebar
if total_cart_items > 0:
    st.sidebar.markdown(f"""
    <div class="cart-notification">
        <h3>🛒 Cart Summary</h3>
        <p><strong>{total_cart_items}</strong> items | <strong>${total_cart_value:.2f}</strong></p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.info("🛒 Your cart is empty")

# Test AI Chat
st.sidebar.markdown("### 💬 Test AI Chat")
if st.session_state.backend_connected:
    user_message = st.sidebar.text_input("Test message:", placeholder="Hello AI")
    if st.sidebar.button("Send Test Message"):
        if user_message:
            with st.spinner("Testing AI..."):
                chat_response = api.chat_with_ai(user_message, st.session_state.user_id)
                st.sidebar.success("AI Response received!")
                st.sidebar.write(chat_response.get("ai_response", "No response"))
else:
    st.sidebar.warning("Backend needed for AI chat")

# Refresh backend connection
if st.sidebar.button("🔄 Refresh Connection"):
    st.session_state.backend_connected = api.check_backend_health()
    st.rerun()

# Main content
st.markdown("""
<div class="main-header">
    <h1>👋 Welcome to RetailMate!</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Your AI-Powered Retail Management Solution</p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>💬 Smart Chat</h3>
        <p>AI-powered customer service and support system</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Analytics</h3>
        <p>Real-time insights and business intelligence</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>📦 Inventory</h3>
        <p>Smart inventory management and tracking</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <h3>🛒 Shopping Cart</h3>
        <p>Seamless shopping experience and cart management</p>
    </div>
    """, unsafe_allow_html=True)

# Quick stats
st.markdown("### 📈 Quick Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Products", "1,234", "12 new today")
with col2:
    st.metric("Active Orders", "89", "-5 from yesterday")
with col3:
    st.metric("Revenue Today", "$12,456", "+8.5%")
with col4:
    st.metric("Cart Items", f"{total_cart_items}", f"${total_cart_value:.2f} total")

# Sample products
st.markdown("### 🌟 Featured Products")
featured_products = [
    {
        'id': 'prod_1',
        'name': 'iPhone 14 Pro',
        'price': 999.99,
        'image': '📱',
        'category': 'Electronics',
        'description': 'Latest iPhone with Pro camera system'
    },
    {
        'id': 'prod_2',
        'name': 'AirPods Pro',
        'price': 249.99,
        'image': '🎧',
        'category': 'Electronics',
        'description': 'Active noise cancellation wireless earbuds'
    }
]

product_cols = st.columns(2)
for i, product in enumerate(featured_products):
    with product_cols[i % 2]:
        st.markdown(f"""
        <div class="product-card">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{product['image']}</div>
                <h3 style="color: #333; margin: 0.5rem 0;">{product['name']}</h3>
                <p style="color: #666; margin: 0.5rem 0; font-size: 0.9rem;">{product['description']}</p>
                <p style="color: #667eea; font-weight: bold; font-size: 1.2rem; margin: 1rem 0;">${product['price']:.2f}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🛒 Add to Cart", key=f"add_product_{product['id']}"):
            if st.session_state.backend_connected:
                result = api.add_to_cart(st.session_state.user_id, product['id'], 1)
                if result.get("success", False):
                    st.success(f"Added {product['name']} to cart!")
                    st.rerun()
                else:
                    st.error("Failed to add item to cart")
            else:
                # Fallback to session state
                cart_item = {
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': 1,
                    'image': product['image']
                }
                st.session_state.cart_items.append(cart_item)
                st.success(f"Added {product['name']} to cart!")
                st.rerun()

# Footer
st.markdown("---")
backend_status = "✅ Connected" if st.session_state.backend_connected else "❌ Disconnected"
st.markdown(f"""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>🚀 RetailMate v1.0 | Backend: {backend_status}</p>
</div>
""", unsafe_allow_html=True)