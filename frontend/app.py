import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import warnings
import requests
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional

# Suppress specific deprecation warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='_plotly_utils')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Backend API Configuration
API_BASE_URL = "http://localhost:8000"  # Change this to your backend URL
API_TIMEOUT = 10

# Page configuration
st.set_page_config(
    page_title="RetailMate - Smart Retail Management",
    page_icon="🛍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user_123"  # In production, get from auth
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
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    @staticmethod
    def get_cart_contents(user_id: str) -> Dict:
        """Get cart contents from backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/cart/{user_id}", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return {"items": [], "total": 0}
        except Exception as e:
            st.error(f"Error fetching cart: {e}")
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
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            st.error(f"Error adding to cart: {e}")
            return {"success": False}
    
    @staticmethod
    def get_cart_summary(user_id: str) -> Dict:
        """Get cart summary from backend"""
        try:
            response = requests.get(f"{API_BASE_URL}/cart/{user_id}/summary", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            return {"total_items": 0, "total_value": 0}
        except Exception as e:
            return {"total_items": 0, "total_value": 0}
    
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
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"recommended_products": []}
        except Exception as e:
            st.error(f"Error getting recommendations: {e}")
            return {"recommended_products": []}
    
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
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"ai_response": "Sorry, I'm having trouble connecting."}
        except Exception as e:
            st.error(f"Error chatting with AI: {e}")
            return {"ai_response": "Sorry, I'm having trouble connecting."}
    
    @staticmethod
    def get_upcoming_events() -> List[Dict]:
        """Get upcoming calendar events"""
        try:
            response = requests.get(f"{API_BASE_URL}/calendar/events", timeout=API_TIMEOUT)
            if response.status_code == 200:
                return response.json().get("events", [])
            return []
        except Exception as e:
            return []

# Check backend connection
api = BackendAPI()
st.session_state.backend_connected = api.check_backend_health()

# Custom CSS for beautiful styling
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
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 1rem;
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
    
    .product-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-color: #667eea;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
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
    
    .ai-chat-container {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .event-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Get cart summary from backend
if st.session_state.backend_connected:
    cart_summary = api.get_cart_summary(st.session_state.user_id)
    total_cart_items = cart_summary.get("total_items", 0)
    total_cart_value = cart_summary.get("total_value", 0)
else:
    # Fallback to session state
    total_cart_items = len(st.session_state.cart_items)
    total_cart_value = sum(item.get('price', 0) * item.get('quantity', 1) for item in st.session_state.cart_items)

# Sidebar styling
st.sidebar.markdown("""
<div class="sidebar-logo">
    <h1 style="color: white; margin: 0;">🛍 RetailMate</h1>
    <p style="color: white; margin: 0; font-size: 0.9rem;">Smart Retail Management</p>
</div>
""", unsafe_allow_html=True)

# Backend connection status
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
    st.sidebar.warning("Some features may be limited without backend connection")

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

# AI Chat in sidebar
st.sidebar.markdown("### 💬 Quick AI Chat")
with st.sidebar.expander("Chat with AI Assistant"):
    user_message = st.text_input("Ask me anything...", placeholder="e.g., Show me laptops under $1000")
    if st.button("Send Message"):
        if user_message and st.session_state.backend_connected:
            with st.spinner("AI is thinking..."):
                chat_response = api.chat_with_ai(
                    user_message,
                    st.session_state.user_id,
                    st.session_state.conversation_id
                )
                st.session_state.conversation_id = chat_response.get("conversation_id")
                st.success("AI Response:")
                st.write(chat_response.get("ai_response", "No response"))
                
                # Show recommended products if any
                recommended = chat_response.get("recommended_products", [])
                if recommended:
                    st.write("**Recommended Products:**")
                    for product in recommended[:3]:  # Show first 3
                        st.write(f"• {product.get('name', 'Unknown')} - ${product.get('price', 0):.2f}")
        elif not st.session_state.backend_connected:
            st.error("Backend not connected. Please check your connection.")

st.sidebar.success("🎯 Choose a page above to get started!")

# Navigation info
st.sidebar.markdown("### 📋 Navigation")
st.sidebar.info("""
- 💬 Chat: AI-powered customer service
- 📊 Analytics: Business insights & reports  
- 📦 Inventory: Stock management system
- 🛒 Cart: Shopping cart management
""")

# Quick actions
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🛒 View Cart"):
    st.switch_page("pages/cart.py")

if st.sidebar.button("🔍 Search Products"):
    search_query = st.sidebar.text_input("Search for products...")
    if search_query and st.session_state.backend_connected:
        recommendations = api.get_shopping_recommendations(search_query, st.session_state.user_id)
        if recommendations.get("recommended_products"):
            st.sidebar.success(f"Found {len(recommendations['recommended_products'])} products!")
        else:
            st.sidebar.warning("No products found")

# Main content
st.markdown("""
<div class="main-header">
    <h1>👋 Welcome to RetailMate!</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Your AI-Powered Retail Management Solution</p>
</div>
""", unsafe_allow_html=True)

# Create columns for feature cards
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

# Show upcoming events if backend is connected
if st.session_state.backend_connected:
    events = api.get_upcoming_events()
    if events:
        st.markdown("### 📅 Upcoming Events")
        for event in events[:3]:  # Show first 3 events
            st.markdown(f"""
            <div class="event-card">
                <h4>{event.get('title', 'Event')}</h4>
                <p>📅 {event.get('date', 'No date')} | 🕐 {event.get('time', 'No time')}</p>
                <p>{event.get('description', 'No description')}</p>
            </div>
            """, unsafe_allow_html=True)

# Quick stats section
st.markdown("### 📈 Quick Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Products",
        value="1,234",
        delta="12 new today"
    )

with col2:
    st.metric(
        label="Active Orders",
        value="89",
        delta="-5 from yesterday"
    )

with col3:
    st.metric(
        label="Revenue Today",
        value="$12,456",
        delta="+8.5%"
    )

with col4:
    st.metric(
        label="Cart Items",
        value=f"{total_cart_items}",
        delta=f"${total_cart_value:.2f} total"
    )

# Featured Products Section
st.markdown("### 🌟 Featured Products")

# Sample product data - in production, this would come from your backend
featured_products = [
    {
        'id': 'prod_1',
        'name': 'iPhone 14 Pro',
        'price': 999.99,
        'image': '📱',
        'category': 'Electronics',
        'rating': 4.8,
        'description': 'Latest iPhone with Pro camera system'
    },
    {
        'id': 'prod_2',
        'name': 'AirPods Pro',
        'price': 249.99,
        'image': '🎧',
        'category': 'Electronics',
        'rating': 4.6,
        'description': 'Active noise cancellation wireless earbuds'
    },
    {
        'id': 'prod_3',
        'name': 'MacBook Air M2',
        'price': 1199.99,
        'image': '💻',
        'category': 'Electronics',
        'rating': 4.9,
        'description': 'Lightweight laptop with M2 chip'
    },
    {
        'id': 'prod_4',
        'name': 'iPad Pro',
        'price': 799.99,
        'image': '📱',
        'category': 'Electronics',
        'rating': 4.7,
        'description': 'Professional tablet with M2 chip'
    }
]

# Display products in a grid
product_cols = st.columns(2)

for i, product in enumerate(featured_products):
    with product_cols[i % 2]:
        st.markdown(f"""
        <div class="product-card">
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{product['image']}</div>
                <h3 style="color: #333; margin: 0.5rem 0;">{product['name']}</h3>
                <p style="color: #666; margin: 0.5rem 0; font-size: 0.9rem;">{product['description']}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0;">
                    <p style="color: #667eea; font-weight: bold; font-size: 1.2rem; margin: 0;">${product['price']:.2f}</p>
                    <p style="color: #ffa500; margin: 0;">⭐ {product['rating']}/5</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add to cart button
        if st.button(f"🛒 Add to Cart", key=f"add_product_{product['id']}"):
            if st.session_state.backend_connected:
                # Add to cart via backend
                result = api.add_to_cart(st.session_state.user_id, product['id'], 1)
                if result.get("success", False):
                    st.success(f"Added {product['name']} to cart!")
                    st.rerun()
                else:
                    st.error("Failed to add item to cart")
            else:
                # Fallback to session state
                existing_item = next((item for item in st.session_state.cart_items if item['id'] == product['id']), None)
                
                if existing_item:
                    existing_item['quantity'] += 1
                    st.success(f"Updated {product['name']} quantity in cart!")
                else:
                    cart_item = {
                        'id': product['id'],
                        'name': product['name'],
                        'price': product['price'],
                        'quantity': 1,
                        'image': product['image'],
                        'category': product['category'],
                        'description': product['description']
                    }
                    st.session_state.cart_items.append(cart_item)
                    st.success(f"Added {product['name']} to cart!")
                
                st.rerun()

# AI Recommendations Section
if st.session_state.backend_connected:
    st.markdown("### 🤖 AI Recommendations")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        recommendation_query = st.text_input(
            "What are you looking for?",
            placeholder="e.g., I need a laptop for work, budget under $1500"
        )
    
    with col2:
        if st.button("Get Recommendations", type="primary"):
            if recommendation_query:
                with st.spinner("AI is finding the best products for you..."):
                    recommendations = api.get_shopping_recommendations(
                        recommendation_query,
                        st.session_state.user_id
                    )
                    
                    recommended_products = recommendations.get("recommended_products", [])
                    ai_response = recommendations.get("ai_response", "")
                    
                    if ai_response:
                        st.success("AI Response:")
                        st.write(ai_response)
                    
                    if recommended_products:
                        st.markdown("**Recommended Products:**")
                        for product in recommended_products[:4]:  # Show first 4
                            col_prod1, col_prod2, col_prod3 = st.columns([1, 3, 1])
                            
                            with col_prod1:
                                st.write(product.get('emoji', '📦'))
                            
                            with col_prod2:
                                st.write(f"**{product.get('name', 'Unknown Product')}**")
                                st.write(f"${product.get('price', 0):.2f}")
                                st.write(product.get('description', 'No description'))
                            
                            with col_prod3:
                                if st.button("Add", key=f"rec_{product.get('id', 'unknown')}"):
                                    result = api.add_to_cart(
                                        st.session_state.user_id,
                                        product.get('id', 'unknown'),
                                        1
                                    )
                                    if result.get("success", False):
                                        st.success("Added to cart!")
                                        st.rerun()
                    else:
                        st.info("No specific product recommendations available.")

# Recent activity
st.markdown("### 📋 Recent Activity")

# Sample data for recent activity
recent_data = pd.DataFrame({
    'Time': ['2 min ago', '5 min ago', '12 min ago', '1 hour ago', '2 hours ago'],
    'Activity': [
        '🛒 New order #1234 received',
        '💬 Customer chat resolved',
        '📦 Low stock alert: iPhone Cases',
        '📊 Daily report generated',
        '🔄 Inventory sync completed'
    ],
    'Status': ['Active', 'Completed', 'Warning', 'Completed', 'Completed']
})

st.dataframe(
    recent_data,
    use_container_width=True,
    hide_index=True
)

# Cart analytics if items exist
if total_cart_items > 0:
    st.markdown("### 🛒 Cart Analytics")
    
    col1, col2 = st.columns(2)
    
    # Get cart data for analytics
    if st.session_state.backend_connected:
        cart_data = api.get_cart_contents(st.session_state.user_id)
        cart_items = cart_data.get("items", [])
    else:
        cart_items = st.session_state.cart_items
    
    if cart_items:
        with col1:
            # Cart items chart
            cart_df = pd.DataFrame(cart_items)
            if not cart_df.empty and 'name' in cart_df.columns and 'quantity' in cart_df.columns:
                fig_cart = px.bar(
                    cart_df,
                    x='name',
                    y='quantity',
                    title='Items in Cart',
                    color='quantity',
                    color_continuous_scale='Viridis'
                )
                fig_cart.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#333')
                )
                st.plotly_chart(fig_cart, use_container_width=True)
        
        with col2:
            # Cart value distribution
            if not cart_df.empty and 'price' in cart_df.columns:
                cart_df['total_value'] = cart_df['price'] * cart_df['quantity']
                fig_pie = px.pie(
                    cart_df,
                    values='total_value',
                    names='name',
                    title='Cart Value Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#333')
                )
                st.plotly_chart(fig_pie, use_container_width=True)

# Sales performance chart
st.markdown("### 📈 Sales Performance")

# Sample sales data
dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
sales_data = pd.DataFrame({
    'Date': dates,
    'Sales': [1200 + i*50 + (i%7)*200 for i in range(len(dates))],
    'Orders': [45 + i*2 + (i%7)*8 for i in range(len(dates))]
})

fig_sales = go.Figure()
fig_sales.add_trace(go.Scatter(
    x=sales_data['Date'],
    y=sales_data['Sales'],
    mode='lines+markers',
    name='Sales ($)',
    line=dict(color='#667eea', width=3)
))

fig_sales.update_layout(
    title='Daily Sales Performance',
    xaxis_title='Date',
    yaxis_title='Sales ($)',
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#333')
)

st.plotly_chart(fig_sales, use_container_width=True)

# Footer
st.markdown("---")
backend_status = "✅ Connected" if st.session_state.backend_connected else "❌ Disconnected"
st.markdown(f"""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🚀 RetailMate v1.0 - Empowering Your Retail Business</p>
    <p>Built with ❤ using Streamlit | 🛒 Cart: {total_cart_items} items (${total_cart_value:.2f}) | Backend: {backend_status}</p>
</div>
""", unsafe_allow_html=True)