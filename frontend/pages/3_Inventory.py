import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='_plotly_utils')
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas')

# Or suppress all FutureWarnings if you prefer (less specific)
# warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(page_title="Inventory Management", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .inventory-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .inventory-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #2a5298;
    }
    
    .alert-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: linear-gradient(135deg, #2ed573 0%, #1e90ff 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
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
<div class="inventory-header">
    <h1>📦 Inventory Management</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem;">Smart Stock Management & Tracking System</p>
</div>
""", unsafe_allow_html=True)

# Create sample inventory data
@st.cache_data
def load_inventory_data():
    np.random.seed(42)
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Beauty']
    
    data = []
    for i in range(150):
        data.append({
            'Product ID': f'PRD-{1000 + i}',
            'Product Name': f'Product {i+1}',
            'Category': np.random.choice(categories),
            'Current Stock': np.random.randint(0, 500),
            'Min Stock Level': np.random.randint(10, 50),
            'Max Stock Level': np.random.randint(100, 1000),
            'Unit Price': round(np.random.uniform(5, 500), 2),
            'Supplier': f'Supplier {np.random.randint(1, 20)}',
            'Last Updated': datetime.now() - timedelta(days=np.random.randint(0, 30)),
            'Status': np.random.choice(['In Stock', 'Low Stock', 'Out of Stock', 'Overstocked'], p=[0.6, 0.2, 0.1, 0.1])
        })
    
    return pd.DataFrame(data)

# Load data
inventory_df = load_inventory_data()

# Sidebar filters
st.sidebar.markdown("### 🎛️ Filters")

# Category filter
categories = ['All'] + sorted(inventory_df['Category'].unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

# Status filter
statuses = ['All'] + sorted(inventory_df['Status'].unique().tolist())
selected_status = st.sidebar.selectbox("Status", statuses)

# Stock level filter
min_stock, max_stock = st.sidebar.slider(
    "Stock Range", 
    min_value=0, 
    max_value=int(inventory_df['Current Stock'].max()),
    value=(0, int(inventory_df['Current Stock'].max()))
)

# Apply filters
filtered_df = inventory_df.copy()
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]
if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
filtered_df = filtered_df[
    (filtered_df['Current Stock'] >= min_stock) & 
    (filtered_df['Current Stock'] <= max_stock)
]

# Key metrics
st.markdown("### 📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_products = len(filtered_df)
    st.metric("Total Products", total_products)

with col2:
    low_stock_count = len(filtered_df[filtered_df['Current Stock'] <= filtered_df['Min Stock Level']])
    st.metric("Low Stock Items", low_stock_count, delta=f"{low_stock_count} items")

with col3:
    out_of_stock = len(filtered_df[filtered_df['Current Stock'] == 0])
    st.metric("Out of Stock", out_of_stock)

with col4:
    total_value = (filtered_df['Current Stock'] * filtered_df['Unit Price']).sum()
    st.metric("Total Inventory Value", f"${total_value:,.2f}")

# Alerts section
st.markdown("### 🚨 Inventory Alerts")

col1, col2 = st.columns(2)

with col1:
    low_stock_items = filtered_df[filtered_df['Current Stock'] <= filtered_df['Min Stock Level']]
    if len(low_stock_items) > 0:
        st.markdown("#### ⚠️ Low Stock Alerts")
        for _, item in low_stock_items.head(5).iterrows():
            st.markdown(f"""
            <div class="alert-card">
                <strong>{item['Product Name']}</strong><br>
                Current: {item['Current Stock']} | Min: {item['Min Stock Level']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-card">
            <strong>✅ All items are well-stocked!</strong>
        </div>
        """, unsafe_allow_html=True)

with col2:
    out_of_stock_items = filtered_df[filtered_df['Current Stock'] == 0]
    if len(out_of_stock_items) > 0:
        st.markdown("#### ❌ Out of Stock")
        for _, item in out_of_stock_items.head(5).iterrows():
            st.markdown(f"""
            <div class="alert-card">
                <strong>{item['Product Name']}</strong><br>
                Category: {item['Category']} | Supplier: {item['Supplier']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-card">
            <strong>✅ No out-of-stock items!</strong>
        </div>
        """, unsafe_allow_html=True)

# Charts section
st.markdown("### 📈 Inventory Analytics")

col1, col2 = st.columns(2)

with col1:
    # Stock distribution by category
    category_stock = filtered_df.groupby('Category')['Current Stock'].sum().reset_index()
    fig_pie = px.pie(
        category_stock, 
        values='Current Stock', 
        names='Category',
        title='Stock Distribution by Category',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    # Status distribution
    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_bar = px.bar(
        status_counts, 
        x='Status', 
        y='Count',
        title='Products by Status',
        color='Status',
        color_discrete_map={
            'In Stock': '#2ed573',
            'Low Stock': '#ffa502',
            'Out of Stock': '#ff4757',
            'Overstocked': '#3742fa'
        }
    )
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

# Inventory value by category
category_value = filtered_df.groupby('Category').apply(
    lambda x: (x['Current Stock'] * x['Unit Price']).sum()
).reset_index()
category_value.columns = ['Category', 'Total Value']

fig_value = px.bar(
    category_value, 
    x='Category', 
    y='Total Value',
    title='Inventory Value by Category',
    color='Total Value',
    color_continuous_scale='Blues'
)
fig_value.update_layout(height=400)
st.plotly_chart(fig_value, use_container_width=True)

# Inventory management actions
st.markdown("### 🔧 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📥 Add New Product"):
        st.success("Product form will open here!")

with col2:
    if st.button("🔄 Bulk Update"):
        st.success("Bulk update panel will open here!")

with col3:
    if st.button("📋 Generate Report"):
        st.success("Report generation started!")

with col4:
    if st.button("🔔 Set Alert"):
        st.success("Alert configuration will open here!")

# Detailed inventory table
st.markdown("### 📋 Detailed Inventory")

# Search functionality
search_term = st.text_input("🔍 Search products...", placeholder="Enter product name or ID")

if search_term:
    filtered_df = filtered_df[
        filtered_df['Product Name'].str.contains(search_term, case=False) |
        filtered_df['Product ID'].str.contains(search_term, case=False)
    ]

# Display table
st.dataframe(
    filtered_df.style.format({
        'Unit Price': '${:.2f}',
        'Last Updated': lambda x: x.strftime('%Y-%m-%d')
    }).map(
        lambda x: 'background-color: #ffebee' if x == 'Out of Stock' else 
                  'background-color: #fff3e0' if x == 'Low Stock' else '', 
        subset=['Status']
    ),
    use_container_width=True,
    hide_index=True
)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>📦 Inventory Management System | Real-time Stock Tracking</p>
</div>
""", unsafe_allow_html=True)