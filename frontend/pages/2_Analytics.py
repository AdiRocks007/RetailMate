import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(page_title="Analytics Dashboard", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .analytics-header {
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
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .insight-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
    }
    
    .kpi-container {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
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

# Header
st.markdown("""
<div class="analytics-header">
    <h1>📊 Analytics Dashboard</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem;">Real-time Business Intelligence & Insights</p>
</div>
""", unsafe_allow_html=True)

# Generate sample data
@st.cache_data
def generate_sample_data():
    np.random.seed(42)
    
    # Date range for the last 30 days
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Sales data
    sales_data = []
    for date in dates:
        daily_sales = np.random.poisson(50)  # Average 50 sales per day
        for _ in range(daily_sales):
            sales_data.append({
                'Date': date,
                'Order_ID': f'ORD-{np.random.randint(10000, 99999)}',
                'Product_Category': np.random.choice(['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Beauty']),
                'Revenue': np.random.lognormal(4, 1),  # Log-normal distribution for revenue
                'Customer_ID': f'CUST-{np.random.randint(1000, 9999)}',
                'Channel': np.random.choice(['Online', 'In-Store', 'Mobile'], p=[0.5, 0.3, 0.2])
            })
    
    sales_df = pd.DataFrame(sales_data)
    
    # Customer data
    customer_data = []
    for i in range(500):
        customer_data.append({
            'Customer_ID': f'CUST-{1000 + i}',
            'Age': np.random.randint(18, 70),
            'Gender': np.random.choice(['Male', 'Female', 'Other']),
            'Location': np.random.choice(['North', 'South', 'East', 'West']),
            'Lifetime_Value': np.random.lognormal(6, 1),
            'Last_Purchase': datetime.now() - timedelta(days=np.random.randint(0, 365)),
            'Satisfaction_Score': np.random.uniform(3.5, 5.0)
        })
    
    customer_df = pd.DataFrame(customer_data)
    
    return sales_df, customer_df

# Load data
sales_df, customer_df = generate_sample_data()

# Sidebar filters
st.sidebar.markdown("### 🎛️ Dashboard Filters")

# Date range selector
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

# Category filter
categories = ['All'] + sorted(sales_df['Product_Category'].unique().tolist())
selected_category = st.sidebar.selectbox("Product Category", categories)

# Channel filter
channels = ['All'] + sorted(sales_df['Channel'].unique().tolist())
selected_channel = st.sidebar.selectbox("Sales Channel", channels)

# Apply filters
filtered_sales = sales_df.copy()
if len(date_range) == 2:
    filtered_sales = filtered_sales[
        (filtered_sales['Date'] >= pd.Timestamp(date_range[0])) & 
        (filtered_sales['Date'] <= pd.Timestamp(date_range[1]))
    ]
if selected_category != 'All':
    filtered_sales = filtered_sales[filtered_sales['Product_Category'] == selected_category]
if selected_channel != 'All':
    filtered_sales = filtered_sales[filtered_sales['Channel'] == selected_channel]

# Key Performance Indicators
st.markdown("### 🎯 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_revenue = filtered_sales['Revenue'].sum()
    revenue_change = np.random.uniform(-5, 15)  # Simulated change
    st.metric(
        "Total Revenue",
        f"${total_revenue:,.2f}",
        delta=f"{revenue_change:.1f}%"
    )

with col2:
    total_orders = len(filtered_sales)
    orders_change = np.random.uniform(-10, 20)
    st.metric(
        "Total Orders",
        f"{total_orders:,}",
        delta=f"{orders_change:.1f}%"
    )

with col3:
    avg_order_value = filtered_sales['Revenue'].mean()
    aov_change = np.random.uniform(-8, 12)
    st.metric(
        "Avg Order Value",
        f"${avg_order_value:.2f}",
        delta=f"{aov_change:.1f}%"
    )

with col4:
    unique_customers = filtered_sales['Customer_ID'].nunique()
    customers_change = np.random.uniform(-5, 25)
    st.metric(
        "Active Customers",
        f"{unique_customers:,}",
        delta=f"{customers_change:.1f}%"
    )

# Advanced KPIs
st.markdown("### 🚀 Advanced Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="kpi-container">
        <h3>Customer Lifetime Value</h3>
        <h2>${:,.2f}</h2>
        <p>Average CLV across all customers</p>
    </div>
    """.format(customer_df['Lifetime_Value'].mean()), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="kpi-container">
        <h3>Customer Satisfaction</h3>
        <h2>{:.1f}/5.0</h2>
        <p>Average satisfaction score</p>
    </div>
    """.format(customer_df['Satisfaction_Score'].mean()), unsafe_allow_html=True)

with col3:
    conversion_rate = np.random.uniform(2.5, 5.0)  # Simulated conversion rate
    st.markdown("""
    <div class="kpi-container">
        <h3>Conversion Rate</h3>
        <h2>{:.1f}%</h2>
        <p>Visitors to customers ratio</p>
    </div>
    """.format(conversion_rate), unsafe_allow_html=True)

# Charts section
st.markdown("### 📈 Sales Analytics")

# Revenue trend
daily_revenue = filtered_sales.groupby('Date')['Revenue'].sum().reset_index()
fig_revenue = px.line(
    daily_revenue, 
    x='Date', 
    y='Revenue',
    title='Daily Revenue Trend',
    color_discrete_sequence=['#667eea']
)
fig_revenue.update_layout(height=400)
st.plotly_chart(fig_revenue, use_container_width=True)

col1, col2 = st.columns(2)

with col1:
    # Sales by category
    category_sales = filtered_sales.groupby('Product_Category')['Revenue'].sum().reset_index()
    fig_category = px.pie(
        category_sales,
        values='Revenue',
        names='Product_Category',
        title='Revenue by Product Category',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_category.update_layout(height=400)
    st.plotly_chart(fig_category, use_container_width=True)

with col2:
    # Sales by channel
    channel_sales = filtered_sales.groupby('Channel')['Revenue'].sum().reset_index()
    fig_channel = px.bar(
        channel_sales,
        x='Channel',
        y='Revenue',
        title='Revenue by Sales Channel',
        color='Channel',
        color_discrete_map={
            'Online': '#667eea',
            'In-Store': '#764ba2',
            'Mobile': '#f093fb'
        }
    )
    fig_channel.update_layout(height=400)
    st.plotly_chart(fig_channel, use_container_width=True)

# Customer Analytics
st.markdown("### 👥 Customer Analytics")

col1, col2 = st.columns(2)

with col1:
    # Customer age distribution
    fig_age = px.histogram(
        customer_df,
        x='Age',
        nbins=20,
        title='Customer Age Distribution',
        color_discrete_sequence=['#4facfe']
    )
    fig_age.update_layout(height=400)
    st.plotly_chart(fig_age, use_container_width=True)

with col2:
    # Customer satisfaction by location
    satisfaction_by_location = customer_df.groupby('Location')['Satisfaction_Score'].mean().reset_index()
    fig_satisfaction = px.bar(
        satisfaction_by_location,
        x='Location',
        y='Satisfaction_Score',
        title='Customer Satisfaction by Location',
        color='Satisfaction_Score',
        color_continuous_scale='RdYlGn'
    )
    fig_satisfaction.update_layout(height=400)
    st.plotly_chart(fig_satisfaction, use_container_width=True)

# Insights and Recommendations
st.markdown("### 💡 AI-Powered Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="insight-card">
        <h3>🎯 Top Insight</h3>
        <p>Electronics category shows 23% higher revenue compared to last month. Consider expanding inventory in this category.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="insight-card">
        <h3>📱 Mobile Opportunity</h3>
        <p>Mobile sales channel has lowest conversion but highest customer satisfaction. Focus on mobile optimization.</p>
    </div>
    """, unsafe_allow_html=True)

# Performance comparison
st.markdown("### 📊 Performance Comparison")

# Create comparison metrics
comparison_data = {
    'Metric': ['Revenue', 'Orders', 'Customers', 'AOV'],
    'Current Period': [
        filtered_sales['Revenue'].sum(),
        len(filtered_sales),
        filtered_sales['Customer_ID'].nunique(),
        filtered_sales['Revenue'].mean()
    ],
    'Previous Period': [
        filtered_sales['Revenue'].sum() * np.random.uniform(0.8, 1.2),
        len(filtered_sales) * np.random.uniform(0.7, 1.3),
        filtered_sales['Customer_ID'].nunique() * np.random.uniform(0.9, 1.1),
        filtered_sales['Revenue'].mean() * np.random.uniform(0.85, 1.15)
    ]
}

comparison_df = pd.DataFrame(comparison_data)
comparison_df['Change %'] = ((comparison_df['Current Period'] - comparison_df['Previous Period']) / comparison_df['Previous Period'] * 100).round(1)

fig_comparison = go.Figure()

fig_comparison.add_trace(go.Bar(
    name='Current Period',
    x=comparison_df['Metric'],
    y=comparison_df['Current Period'],
    marker_color='#667eea'
))

fig_comparison.add_trace(go.Bar(
    name='Previous Period',
    x=comparison_df['Metric'],
    y=comparison_df['Previous Period'],
    marker_color='#764ba2'
))

fig_comparison.update_layout(
    title='Current vs Previous Period Performance',
    barmode='group',
    height=400
)

st.plotly_chart(fig_comparison, use_container_width=True)

# Detailed analytics table
st.markdown("### 📋 Detailed Analytics")

# Top performing products
top_products = filtered_sales.groupby('Product_Category').agg({
    'Revenue': ['sum', 'mean', 'count'],
    'Customer_ID': 'nunique'
}).round(2)

top_products.columns = ['Total Revenue', 'Avg Revenue', 'Total Orders', 'Unique Customers']
top_products = top_products.sort_values('Total Revenue', ascending=False)

st.dataframe(
    top_products.style.format({
        'Total Revenue': '${:,.2f}',
        'Avg Revenue': '${:,.2f}',
        'Total Orders': '{:,}',
        'Unique Customers': '{:,}'
    }).background_gradient(subset=['Total Revenue'], cmap='Blues'),
    use_container_width=True
)

# Forecasting section
st.markdown("### 🔮 Revenue Forecasting")

# Simple forecasting using trend
daily_revenue_sorted = daily_revenue.sort_values('Date')
daily_revenue_sorted['Day_Number'] = range(len(daily_revenue_sorted))

# Calculate trend
z = np.polyfit(daily_revenue_sorted['Day_Number'], daily_revenue_sorted['Revenue'], 1)
p = np.poly1d(z)

# Forecast next 7 days
future_days = range(len(daily_revenue_sorted), len(daily_revenue_sorted) + 7)
future_dates = pd.date_range(start=daily_revenue_sorted['Date'].max() + timedelta(days=1), periods=7, freq='D')
forecast_revenue = p(future_days)

# Create forecast chart
fig_forecast = go.Figure()

fig_forecast.add_trace(go.Scatter(
    x=daily_revenue_sorted['Date'],
    y=daily_revenue_sorted['Revenue'],
    mode='lines+markers',
    name='Actual Revenue',
    line=dict(color='#667eea', width=2)
))

fig_forecast.add_trace(go.Scatter(
    x=future_dates,
    y=forecast_revenue,
    mode='lines+markers',
    name='Forecasted Revenue',
    line=dict(color='#f093fb', width=2, dash='dash')
))

fig_forecast.update_layout(
    title='7-Day Revenue Forecast',
    xaxis_title='Date',
    yaxis_title='Revenue ($)',
    height=400,
    showlegend=True
)

st.plotly_chart(fig_forecast, use_container_width=True)

# Action items
st.markdown("### 🎯 Recommended Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📈 Optimize Marketing"):
        st.success("Marketing optimization strategy will be generated!")

with col2:
    if st.button("🎯 Target Customers"):
        st.success("Customer targeting analysis will be performed!")

with col3:
    if st.button("📊 Generate Report"):
        st.success("Comprehensive analytics report will be created!")

# Export options
st.markdown("### 💾 Export Options")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📄 Export to PDF"):
        st.info("PDF report generation started...")

with col2:
    if st.button("📊 Export to Excel"):
        st.info("Excel file preparation in progress...")

with col3:
    if st.button("📧 Email Report"):
        st.info("Report will be emailed to stakeholders...")

# Real-time monitoring
st.markdown("### 📡 Real-time Monitoring")

# Simulate real-time data
real_time_col1, real_time_col2, real_time_col3 = st.columns(3)

with real_time_col1:
    st.metric("Live Orders", "12", delta="2 in last 5 min")

with real_time_col2:
    st.metric("Active Users", "1,234", delta="56 new")

with real_time_col3:
    st.metric("Conversion Rate", "3.2%", delta="0.3%")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>📊 Advanced Analytics Dashboard | Real-time Business Intelligence</p>
    <p>Last updated: {} | Auto-refresh every 5 minutes</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)