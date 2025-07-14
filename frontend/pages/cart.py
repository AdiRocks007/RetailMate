import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import warnings

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import BackendAPI

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(
    page_title="🛒 Shopping Cart - RetailMate",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration
API_BASE_URL =  "http://127.0.0.1:8000"
API_TIMEOUT = 10

# Backend API Functions
class CartAPI:
    @staticmethod
    def check_backend_health():
        """Check if backend is running and healthy"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except:
            return False

    
    @staticmethod
    def get_cart_contents(user_id: str):
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
    def update_cart_item(user_id: str, product_id: str, quantity: int):
        """Update item quantity in cart"""
        try:
            payload = {"product_id": product_id, "quantity": quantity}
            response = requests.put(
                f"{API_BASE_URL}/cart/{user_id}/update",
                json=payload,
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            st.error(f"Error updating cart: {e}")
            return {"success": False}
    
    @staticmethod
    def remove_cart_item(user_id: str, product_id: str):
        """Remove item from cart"""
        try:
            response = requests.delete(
                f"{API_BASE_URL}/cart/{user_id}/remove/{product_id}",
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            st.error(f"Error removing item: {e}")
            return {"success": False}
    
    @staticmethod
    def clear_cart(user_id: str):
        """Clear entire cart"""
        try:
            response = requests.delete(f"{API_BASE_URL}/cart/{user_id}/clear", timeout=API_TIMEOUT)
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            st.error(f"Error clearing cart: {e}")
            return {"success": False}
    
    @staticmethod
    def apply_promo_code(user_id: str, promo_code: str):
        """Apply promo code to cart"""
        try:
            payload = {"promo_code": promo_code}
            response = requests.post(
                f"{API_BASE_URL}/cart/{user_id}/promo",
                json=payload,
                timeout=API_TIMEOUT
            )
            return response.json() if response.status_code == 200 else {"success": False}
        except Exception as e:
            st.error(f"Error applying promo code: {e}")
            return {"success": False}

# Initialize session state
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []
if 'user_id' not in st.session_state:
    st.session_state.user_id = "demo_user_123"
if 'backend_connected' not in st.session_state:
    st.session_state.backend_connected = False

# Check backend connection
api = CartAPI()
st.session_state.backend_connected = api.check_backend_health()

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
    
    .cart-item {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .cart-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .summary-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .empty-cart {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 3rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        color: #333;
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
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar styling
st.sidebar.markdown("""
<div class="sidebar-logo">
    <h1 style="color: white; margin: 0;">🛒 Cart</h1>
    <p style="color: white; margin: 0; font-size: 0.9rem;">Shopping Cart Management</p>
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
    st.sidebar.warning("Using local cart data")

# Get cart data
if st.session_state.backend_connected:
    cart_data = api.get_cart_contents(st.session_state.user_id)
    cart_items = cart_data.get("items", [])
    cart_total = cart_data.get("total", 0)
else:
    # Fallback to session state with sample data
    if not st.session_state.cart_items:
        st.session_state.cart_items = [
            {
                'id': 'prod_1',
                'name': 'iPhone 14 Pro',
                'price': 999.99,
                'quantity': 1,
                'image': '📱',
                'category': 'Electronics',
                'description': 'Latest iPhone with Pro features'
            },
            {
                'id': 'prod_2',
                'name': 'AirPods Pro',
                'price': 249.99,
                'quantity': 2,
                'image': '🎧',
                'category': 'Electronics',
                'description': 'Wireless earbuds with noise cancellation'
            }
        ]
    cart_items = st.session_state.cart_items
    cart_total = sum(item['price'] * item['quantity'] for item in cart_items)

# Sidebar cart summary
total_items = sum(item['quantity'] for item in cart_items)
st.sidebar.metric("Items in Cart", total_items)
st.sidebar.metric("Total Amount", f"${cart_total:.2f}")

# Quick actions
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🗑️ Clear Cart"):
    if st.session_state.backend_connected:
        result = api.clear_cart(st.session_state.user_id)
        if result.get("success", False):
            st.success("Cart cleared successfully!")
            st.rerun()
    else:
        st.session_state.cart_items = []
        st.rerun()

if st.sidebar.button("🔄 Refresh Cart"):
    st.rerun()

# Main content
st.markdown("""
<div class="main-header">
    <h1>🛒 Your Shopping Cart</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Review and manage your selected items</p>
</div>
""", unsafe_allow_html=True)

# Main cart content
if len(cart_items) == 0:
    st.markdown("""
    <div class="empty-cart">
        <h2>🛒 Your cart is empty</h2>
        <p style="font-size: 1.1rem; margin-top: 1rem;">Looks like you haven't added any items yet.</p>
        <p>Start shopping to see items here!</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 Go to Home"):
        st.switch_page("app.py")
else:
    # Create two columns for cart items and summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📦 Cart Items")
        
        # Display cart items
        for i, item in enumerate(cart_items):
            with st.container():
                st.markdown(f"""
                <div class="cart-item">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center;">
                            <div style="font-size: 3rem; margin-right: 1rem;">{item['image']}</div>
                            <div>
                                <h3 style="margin: 0; color: #333;">{item['name']}</h3>
                                <p style="margin: 0; color: #666; font-size: 0.9rem;">{item.get('description', 'No description')}</p>
                                <p style="margin: 0; color: #667eea; font-weight: bold;">${item['price']:.2f}</p>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; font-size: 1.1rem; font-weight: bold;">Total: ${item['price'] * item['quantity']:.2f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns([1, 1, 1, 2, 2])
                
                with action_col1:
                    if st.button("➖", key=f"dec_{item['id']}"):
                        new_quantity = max(1, item['quantity'] - 1)
                        if st.session_state.backend_connected:
                            result = api.update_cart_item(st.session_state.user_id, item['id'], new_quantity)
                            if result.get("success", False):
                                st.rerun()
                        else:
                            st.session_state.cart_items[i]['quantity'] = new_quantity
                            st.rerun()
                
                with action_col2:
                    st.markdown(f"<center><strong>{item['quantity']}</strong></center>", unsafe_allow_html=True)
                
                with action_col3:
                    if st.button("➕", key=f"inc_{item['id']}"):
                        new_quantity = item['quantity'] + 1
                        if st.session_state.backend_connected:
                            result = api.update_cart_item(st.session_state.user_id, item['id'], new_quantity)
                            if result.get("success", False):
                                st.rerun()
                        else:
                            st.session_state.cart_items[i]['quantity'] = new_quantity
                            st.rerun()
                
                with action_col4:
                    if st.button("❤️ Save Later", key=f"save_{item['id']}"):
                        st.success(f"Saved {item['name']} for later!")
                
                with action_col5:
                    if st.button("🗑️ Remove", key=f"remove_{item['id']}"):
                        if st.session_state.backend_connected:
                            result = api.remove_cart_item(st.session_state.user_id, item['id'])
                            if result.get("success", False):
                                st.rerun()
                        else:
                            st.session_state.cart_items.pop(i)
                            st.rerun()
                
                st.markdown("---")
    
    with col2:
        st.markdown("### 💰 Order Summary")
        
        # Calculate totals
        subtotal = cart_total
        tax = subtotal * 0.08  # 8% tax
        shipping = 15.99 if subtotal < 100 else 0  # Free shipping over $100
        total = subtotal + tax + shipping
        
        st.markdown(f"""
        <div class="summary-card">
            <h3>💳 Payment Summary</h3>
            <div style="text-align: left; margin-top: 1rem;">
                <p><strong>Subtotal:</strong> ${subtotal:.2f}</p>
                <p><strong>Tax (8%):</strong> ${tax:.2f}</p>
                <p><strong>Shipping:</strong> ${shipping:.2f}</p>
                <hr style="border-color: rgba(255,255,255,0.3);">
                <p style="font-size: 1.3rem;"><strong>Total: ${total:.2f}</strong></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Promo code section
        st.markdown("### 🎟️ Promo Code")
        promo_code = st.text_input("Enter promo code", placeholder="SAVE10")
        if st.button("Apply Code"):
            if st.session_state.backend_connected:
                result = api.apply_promo_code(st.session_state.user_id, promo_code)
                if result.get("success", False):
                    st.success("✅ Promo code applied!")
                    st.rerun()
                else:
                    st.error("❌ Invalid promo code")
            else:
                if promo_code.upper() == "SAVE10":
                    st.success("✅ 10% discount applied!")
                else:
                    st.error("❌ Invalid promo code")
        
        # Checkout button
        st.markdown("### 🚀 Checkout")
        if st.button("🛒 Proceed to Checkout", key="checkout"):
            st.success("🎉 Redirecting to checkout...")
            st.balloons()

# Cart analytics
if len(cart_items) > 0:
    st.markdown("### 📊 Cart Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category breakdown
        categories = {}
        for item in cart_items:
            category = item.get('category', 'Other')
            categories[category] = categories.get(category, 0) + item['quantity']
        
        if categories:
            fig_pie = px.pie(
                values=list(categories.values()),
                names=list(categories.keys()),
                title="Items by Category",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333')
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Price distribution
        items_df = pd.DataFrame(cart_items)
        items_df['total_price'] = items_df['price'] * items_df['quantity']
        
        fig_bar = px.bar(
            items_df,
            x='name',
            y='total_price',
            title="Total Price by Item",
            color='total_price',
            color_continuous_scale='Viridis'
        )
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333'),
            xaxis_title="Items",
            yaxis_title="Total Price ($)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Footer
st.markdown("---")
backend_status = "✅ Connected" if st.session_state.backend_connected else "❌ Disconnected"
st.markdown(f"""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🛒 Secure Shopping with RetailMate</p>
    <p>💳 SSL Secured | 🚚 Free returns | Backend: {backend_status}</p>
</div>
""", unsafe_allow_html=True)