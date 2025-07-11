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
</style>
""", unsafe_allow_html=True)

# Sidebar styling
st.sidebar.markdown("""
<div class="sidebar-logo">
    <h1 style="color: white; margin: 0;">🛍 RetailMate</h1>
    <p style="color: white; margin: 0; font-size: 0.9rem;">Smart Retail Management</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.success("🎯 Choose a page above to get started!")

# Navigation info
st.sidebar.markdown("### 📋 Navigation")
st.sidebar.info("""
- *💬 Chat*: AI-powered customer service
- *📊 Analytics*: Business insights & reports  
- *📦 Inventory*: Stock management system
""")

# Main content
st.markdown("""
<div class="main-header">
    <h1>👋 Welcome to RetailMate!</h1>
    <p style="font-size: 1.2rem; margin-top: 1rem;">Your AI-Powered Retail Management Solution</p>
</div>
""", unsafe_allow_html=True)

# Create columns for feature cards
col1, col2, col3 = st.columns(3)

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
        label="Customer Satisfaction",
        value="4.8/5",
        delta="+0.2"
    )

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

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #666;">
    <p>🚀 RetailMate v1.0 - Empowering Your Retail Business</p>
    <p>Built with ❤ using Streamlit</p>
</div>
""", unsafe_allow_html=True)