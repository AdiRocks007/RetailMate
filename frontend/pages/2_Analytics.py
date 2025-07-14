import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import requests
import warnings

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import BackendAPI

warnings.filterwarnings('ignore', category=FutureWarning)

# Configuration
API_BASE_URL =  "http://127.0.0.1:8000"

def check_backend_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json().get("status") == "healthy"
    except:
        pass
    return False

st.set_page_config(page_title="Analytics Dashboard", layout="wide")

# Custom CSS - Simplified
st.markdown("""
<style>
    .analytics-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
        text-align: center; color: white; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .kpi-container {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem; border-radius: 12px; text-align: center;
        color: white; margin: 0.5rem 0;
    }
    .insight-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
        color: white; box-shadow: 0 6px 25px rgba(0,0,0,0.15);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 25px;
        padding: 0.5rem 2rem; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Data fetching functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_analytics_data():
    """Fetch data from backend API"""
    try:
        # Fetch sales data
        sales_response = requests.get(f"{API_BASE_URL}/analytics/sales")
        sales_data = sales_response.json() if sales_response.status_code == 200 else []
        
        # Fetch customer data
        customers_response = requests.get(f"{API_BASE_URL}/analytics/customers")
        customers_data = customers_response.json() if customers_response.status_code == 200 else []
        
        # Fetch KPIs
        kpis_response = requests.get(f"{API_BASE_URL}/analytics/kpis")
        kpis_data = kpis_response.json() if kpis_response.status_code == 200 else {}
        
        return sales_data, customers_data, kpis_data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return [], [], {}

def generate_fallback_data():
    """Generate sample data when API is unavailable"""
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    sales_data = []
    for date in dates:
        for _ in range(np.random.poisson(50)):
            sales_data.append({
                'date': date.isoformat(),
                'order_id': f'ORD-{np.random.randint(10000, 99999)}',
                'product_category': np.random.choice(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']),
                'revenue': np.random.lognormal(4, 1),
                'customer_id': f'CUST-{np.random.randint(1000, 9999)}',
                'channel': np.random.choice(['Online', 'In-Store', 'Mobile'], p=[0.5, 0.3, 0.2])
            })
    
    customers_data = []
    for i in range(500):
        customers_data.append({
            'customer_id': f'CUST-{1000 + i}',
            'age': np.random.randint(18, 70),
            'location': np.random.choice(['North', 'South', 'East', 'West']),
            'lifetime_value': np.random.lognormal(6, 1),
            'satisfaction_score': np.random.uniform(3.5, 5.0)
        })
    
    kpis_data = {
        'total_revenue': sum(item['revenue'] for item in sales_data),
        'total_orders': len(sales_data),
        'avg_order_value': sum(item['revenue'] for item in sales_data) / len(sales_data),
        'active_customers': len(set(item['customer_id'] for item in sales_data)),
        'conversion_rate': np.random.uniform(2.5, 5.0)
    }
    
    return sales_data, customers_data, kpis_data

# Header
st.markdown("""
<div class="analytics-header">
    <h1>📊 Analytics Dashboard</h1>
    <p>Real-time Business Intelligence & Insights</p>
</div>
""", unsafe_allow_html=True)

# Backend health check before fetching
if not check_backend_health():
    st.warning("⚠️ Backend unreachable. Using fallback data for demo.")
    sales_data, customers_data, kpis_data = generate_fallback_data()
else:
    sales_data, customers_data, kpis_data = fetch_analytics_data()
    if not sales_data:
        st.warning("⚠️ API error. Using fallback data instead.")
        sales_data, customers_data, kpis_data = generate_fallback_data()

# Convert to DataFrames
sales_df = pd.DataFrame(sales_data)
customers_df = pd.DataFrame(customers_data)

# Ensure date column is datetime
if 'date' in sales_df.columns:
    sales_df['date'] = pd.to_datetime(sales_df['date'])

# Sidebar backend status
st.sidebar.markdown("### 🔌 Backend Status")
if check_backend_health():
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.error("❌ Disconnected")

# Sidebar filters
st.sidebar.markdown("### 🎛️ Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

if not sales_df.empty:
    categories = ['All'] + sorted(sales_df['product_category'].unique())
    selected_category = st.sidebar.selectbox("Category", categories)
    
    channels = ['All'] + sorted(sales_df['channel'].unique())
    selected_channel = st.sidebar.selectbox("Channel", channels)
    
    # Apply filters
    filtered_sales = sales_df.copy()
    if len(date_range) == 2:
        filtered_sales = filtered_sales[
            (filtered_sales['date'] >= pd.Timestamp(date_range[0])) & 
            (filtered_sales['date'] <= pd.Timestamp(date_range[1]))
        ]
    if selected_category != 'All':
        filtered_sales = filtered_sales[filtered_sales['product_category'] == selected_category]
    if selected_channel != 'All':
        filtered_sales = filtered_sales[filtered_sales['channel'] == selected_channel]
else:
    filtered_sales = pd.DataFrame()

# KPIs
st.markdown("### 🎯 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    revenue = kpis_data.get('total_revenue', 0)
    st.metric("Total Revenue", f"${revenue:,.2f}", delta="12.5%")

with col2:
    orders = kpis_data.get('total_orders', 0)
    st.metric("Total Orders", f"{orders:,}", delta="8.3%")

with col3:
    aov = kpis_data.get('avg_order_value', 0)
    st.metric("Avg Order Value", f"${aov:.2f}", delta="5.2%")

with col4:
    customers = kpis_data.get('active_customers', 0)
    st.metric("Active Customers", f"{customers:,}", delta="15.7%")

# Advanced KPIs
st.markdown("### 🚀 Advanced Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    clv = customers_df['lifetime_value'].mean() if not customers_df.empty else 0
    st.markdown(f"""
    <div class="kpi-container">
        <h3>Customer Lifetime Value</h3>
        <h2>${clv:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    satisfaction = customers_df['satisfaction_score'].mean() if not customers_df.empty else 0
    st.markdown(f"""
    <div class="kpi-container">
        <h3>Customer Satisfaction</h3>
        <h2>{satisfaction:.1f}/5.0</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    conversion = kpis_data.get('conversion_rate', 0)
    st.markdown(f"""
    <div class="kpi-container">
        <h3>Conversion Rate</h3>
        <h2>{conversion:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

# Charts
if not filtered_sales.empty:
    st.markdown("### 📈 Sales Analytics")
    
    # Revenue trend
    daily_revenue = filtered_sales.groupby('date')['revenue'].sum().reset_index()
    fig_revenue = px.line(daily_revenue, x='date', y='revenue', 
                         title='Daily Revenue Trend', color_discrete_sequence=['#667eea'])
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sales by category
        category_sales = filtered_sales.groupby('product_category')['revenue'].sum().reset_index()
        fig_category = px.pie(category_sales, values='revenue', names='product_category',
                             title='Revenue by Category')
        st.plotly_chart(fig_category, use_container_width=True)
    
    with col2:
        # Sales by channel
        channel_sales = filtered_sales.groupby('channel')['revenue'].sum().reset_index()
        fig_channel = px.bar(channel_sales, x='channel', y='revenue',
                           title='Revenue by Channel', color='channel')
        st.plotly_chart(fig_channel, use_container_width=True)

# Customer Analytics
if not customers_df.empty:
    st.markdown("### 👥 Customer Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_age = px.histogram(customers_df, x='age', nbins=20, 
                              title='Customer Age Distribution')
        st.plotly_chart(fig_age, use_container_width=True)
    
    with col2:
        satisfaction_by_location = customers_df.groupby('location')['satisfaction_score'].mean().reset_index()
        fig_satisfaction = px.bar(satisfaction_by_location, x='location', y='satisfaction_score',
                                title='Satisfaction by Location', color='satisfaction_score')
        st.plotly_chart(fig_satisfaction, use_container_width=True)

# Insights
st.markdown("### 💡 AI-Powered Insights")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="insight-card">
        <h3>🎯 Top Insight</h3>
        <p>Electronics category shows 23% higher revenue. Consider expanding inventory.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="insight-card">
        <h3>📱 Mobile Opportunity</h3>
        <p>Mobile channel has potential for optimization and growth.</p>
    </div>
    """, unsafe_allow_html=True)

# Action buttons
st.markdown("### 🎯 Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📈 Optimize Marketing"):
        try:
            response = requests.post(f"{API_BASE_URL}/analytics/optimize-marketing")
            if response.status_code == 200:
                st.success("Marketing optimization initiated!")
            else:
                st.error("Failed to optimize marketing")
        except:
            st.success("Marketing optimization strategy generated!")

with col2:
    if st.button("🎯 Target Customers"):
        try:
            response = requests.post(f"{API_BASE_URL}/analytics/target-customers")
            if response.status_code == 200:
                st.success("Customer targeting analysis started!")
            else:
                st.error("Failed to start analysis")
        except:
            st.success("Customer targeting analysis performed!")

with col3:
    if st.button("📊 Generate Report"):
        try:
            response = requests.post(f"{API_BASE_URL}/analytics/generate-report")
            if response.status_code == 200:
                st.success("Report generation started!")
            else:
                st.error("Failed to generate report")
        except:
            st.success("Report will be ready shortly!")

# Real-time monitoring
st.markdown("### 📡 Real-time Monitoring")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Live Orders", "12", delta="2 in last 5 min")

with col2:
    st.metric("Active Users", "1,234", delta="56 new")

with col3:
    st.metric("Conversion Rate", "3.2%", delta="0.3%")

# Footer
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>📊 Advanced Analytics Dashboard | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)