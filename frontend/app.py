import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='_plotly_utils')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Or suppress all FutureWarnings if you prefer (less specific)
# warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(
    page_title="RetailMate - Smart Retail Management",
    page_icon="🛍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for cart
if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []

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
        height: 220px; /* Fixed height for uniformity */
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
    
    .add-to-cart-btn {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .cart-badge {
        background: #ff6b6b;
        color: white;
        border-radius: 50%;
        padding: 0.2rem 0.6rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Calculate cart totals for sidebar
total_cart_items = len(st.session_state.cart_items)
total_cart_value = sum(item.get('price', 0) * item.get('quantity', 1) for item in st.session_state.cart_items)

# Sidebar styling
st.sidebar.markdown("""
<div class="sidebar-logo">
    <h1 style="color: white; margin: 0;">🛍 RetailMate</h1>
    <p style="color: white; margin: 0; font-size: 0.9rem;">Smart Retail Management</p>
</div>
""", unsafe_allow_html=True)

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
    st.info("Search functionality coming soon!")

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

# Sample product data
featured_products = [
    {
        'id': 1,
        'name': 'iPhone 14 Pro',
        'price': 999.99,
        'image': '📱',
        'category': 'Electronics',
        'rating': 4.8,
        'description': 'Latest iPhone with Pro camera system'
    },
    {
        'id': 2,
        'name': 'AirPods Pro',
        'price': 249.99,
        'image': '🎧',
        'category': 'Electronics',
        'rating': 4.6,
        'description': 'Active noise cancellation wireless earbuds'
    },
    {
        'id': 3,
        'name': 'MacBook Air M2',
        'price': 1199.99,
        'image': '💻',
        'category': 'Electronics',
        'rating': 4.9,
        'description': 'Lightweight laptop with M2 chip'
    },
    {
        'id': 4,
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
            # Check if product already in cart
            existing_item = next((item for item in st.session_state.cart_items if item['id'] == product['id']), None)
            
            if existing_item:
                # Increase quantity if already in cart
                existing_item['quantity'] += 1
                st.success(f"Updated {product['name']} quantity in cart!")
            else:
                # Add new item to cart
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
            
            # Show cart update notification
            st.rerun()

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
    
    with col1:
        # Cart items chart
        cart_df = pd.DataFrame(st.session_state.cart_items)
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
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🚀 RetailMate v1.0 - Empowering Your Retail Business</p>
    <p>Built with ❤ using Streamlit | 🛒 Cart: {total_items} items (${total_value:.2f})</p>
</div>
""".format(total_items=total_cart_items, total_value=total_cart_value), unsafe_allow_html=True)