import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='_plotly_utils')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Page configuration
st.set_page_config(
    page_title="🛒 Shopping Cart - RetailMate",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    .promo-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: #333;
        border: 2px solid #f7a072;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }
    
    .checkout-btn {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 1rem 2rem;
        font-weight: bold;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .remove-btn {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.3rem 1rem;
        font-size: 0.8rem;
        transition: all 0.3s ease;
    }
    
    .quantity-controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin: 0.5rem 0;
    }
    
    .quantity-btn {
        background: #667eea;
        color: white;
        border: none;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quantity-btn:hover {
        background: #764ba2;
        transform: scale(1.1);
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

# Initialize session state for cart
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = [
        {
            'id': 1,
            'name': 'iPhone 14 Pro',
            'price': 999.99,
            'quantity': 1,
            'image': '📱',
            'category': 'Electronics',
            'description': 'Latest iPhone with Pro features'
        },
        {
            'id': 2,
            'name': 'AirPods Pro',
            'price': 249.99,
            'quantity': 2,
            'image': '🎧',
            'category': 'Electronics',
            'description': 'Wireless earbuds with noise cancellation'
        },
        {
            'id': 3,
            'name': 'MacBook Air M2',
            'price': 1199.99,
            'quantity': 1,
            'image': '💻',
            'category': 'Electronics',
            'description': 'Lightweight laptop with M2 chip'
        }
    ]

# Sidebar cart summary
st.sidebar.markdown("### 🛒 Cart Summary")
total_items = sum(item['quantity'] for item in st.session_state.cart_items)
total_amount = sum(item['price'] * item['quantity'] for item in st.session_state.cart_items)

st.sidebar.metric("Items in Cart", total_items)
st.sidebar.metric("Total Amount", f"${total_amount:.2f}")

# Quick actions
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🗑️ Clear Cart"):
    st.session_state.cart_items = []
    st.rerun()

if st.sidebar.button("💾 Save Cart"):
    st.sidebar.success("Cart saved successfully!")

if st.sidebar.button("🔄 Refresh"):
    st.rerun()

# Main content
st.markdown("""
<div class="main-header">
    <h1>🛒 Your Shopping Cart</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Review and manage your selected items</p>
</div>
""", unsafe_allow_html=True)

# Main cart content
if len(st.session_state.cart_items) == 0:
    st.markdown("""
    <div class="empty-cart">
        <h2>🛒 Your cart is empty</h2>
        <p style="font-size: 1.1rem; margin-top: 1rem;">Looks like you haven't added any items yet.</p>
        <p>Start shopping to see items here!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Create two columns for cart items and summary
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📦 Cart Items")
        
        # Display cart items
        for i, item in enumerate(st.session_state.cart_items):
            with st.container():
                st.markdown(f"""
                <div class="cart-item">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center;">
                            <div style="font-size: 3rem; margin-right: 1rem;">{item['image']}</div>
                            <div>
                                <h3 style="margin: 0; color: #333;">{item['name']}</h3>
                                <p style="margin: 0; color: #666; font-size: 0.9rem;">{item['description']}</p>
                                <p style="margin: 0; color: #667eea; font-weight: bold;">${item['price']:.2f}</p>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; font-size: 1.1rem; font-weight: bold;">Total: ${item['price'] * item['quantity']:.2f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Quantity controls and action buttons - using horizontal layout
                st.markdown("---")
                
                # Create action buttons in a single row
                action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns([1, 1, 1, 2, 2])
                
                with action_col1:
                    if st.button("➖", key=f"dec_{item['id']}"):
                        if item['quantity'] > 1:
                            st.session_state.cart_items[i]['quantity'] -= 1
                            st.rerun()
                
                with action_col2:
                    st.markdown(f"<center><strong>{item['quantity']}</strong></center>", unsafe_allow_html=True)
                
                with action_col3:
                    if st.button("➕", key=f"inc_{item['id']}"):
                        st.session_state.cart_items[i]['quantity'] += 1
                        st.rerun()
                
                with action_col4:
                    if st.button("❤️ Save for Later", key=f"save_{item['id']}"):
                        st.success(f"Saved {item['name']} for later!")
                
                with action_col5:
                    if st.button("🗑️ Remove", key=f"remove_{item['id']}"):
                        st.session_state.cart_items.pop(i)
                        st.rerun()
                
                st.markdown("---")
    
    with col2:
        st.markdown("### 💰 Order Summary")
        
        # Calculate totals
        subtotal = sum(item['price'] * item['quantity'] for item in st.session_state.cart_items)
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
        with st.container():
            promo_code = st.text_input("Enter promo code", placeholder="SAVE10")
            if st.button("Apply Code"):
                if promo_code.upper() == "SAVE10":
                    st.success("✅ 10% discount applied!")
                else:
                    st.error("❌ Invalid promo code")
        
        # Checkout button
        st.markdown("### 🚀 Checkout")
        if st.button("🛒 Proceed to Checkout", key="checkout"):
            st.success("🎉 Redirecting to checkout...")
            st.balloons()
        
        # Additional options
        st.markdown("### 📋 Additional Options")
        st.markdown("""
        <div class="promo-card">
            <h4>🚚 Shipping Options</h4>
            <p>• Standard (5-7 days): $15.99</p>
            <p>• Express (2-3 days): $25.99</p>
            <p>• Overnight: $35.99</p>
            <p>• Free shipping on orders over $100!</p>
        </div>
        """, unsafe_allow_html=True)

# Recommendations section
st.markdown("### 🌟 You Might Also Like")

# Sample recommendation data
recommendations = [
    {'name': 'iPhone Case', 'price': 29.99, 'image': '📱', 'rating': 4.5},
    {'name': 'Wireless Charger', 'price': 39.99, 'image': '🔌', 'rating': 4.8},
    {'name': 'Screen Protector', 'price': 19.99, 'image': '🛡️', 'rating': 4.3},
    {'name': 'Bluetooth Speaker', 'price': 79.99, 'image': '🔊', 'rating': 4.6}
]

rec_cols = st.columns(4)
for i, rec in enumerate(recommendations):
    with rec_cols[i]:
        st.markdown(f"""
        <div class="cart-item" style="text-align: center;">
            <div style="font-size: 2rem;">{rec['image']}</div>
            <h4>{rec['name']}</h4>
            <p style="color: #667eea; font-weight: bold;">${rec['price']:.2f}</p>
            <p>⭐ {rec['rating']}/5</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Add to Cart", key=f"add_rec_{i}"):
            new_item = {
                'id': len(st.session_state.cart_items) + 1,
                'name': rec['name'],
                'price': rec['price'],
                'quantity': 1,
                'image': rec['image'],
                'category': 'Accessories',
                'description': f'{rec["name"]} - Highly rated product'
            }
            st.session_state.cart_items.append(new_item)
            st.success(f"Added {rec['name']} to cart!")
            st.rerun()

# Cart analytics
st.markdown("### 📊 Cart Analytics")

if len(st.session_state.cart_items) > 0:
    col1, col2 = st.columns(2)
    
    with col1:
        # Category breakdown
        categories = {}
        for item in st.session_state.cart_items:
            category = item['category']
            if category not in categories:
                categories[category] = 0
            categories[category] += item['quantity']
        
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
        items_df = pd.DataFrame(st.session_state.cart_items)
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
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🛒 Secure Shopping with RetailMate</p>
    <p>💳 We accept all major credit cards | 🔒 SSL Secured | 🚚 Free returns</p>
</div>
""", unsafe_allow_html=True)