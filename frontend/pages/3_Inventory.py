import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import warnings
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import BackendAPI

warnings.filterwarnings('ignore', category=FutureWarning)

# Page configuration
st.set_page_config(page_title="Inventory Management", layout="wide")

# API Configuration
API_BASE_URL =  "http://127.0.0.1:8000"

# Backend API functions
def check_backend_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json().get("status") == "healthy"
    except:
        pass
    return False

# Backend API functions
@st.cache_data(ttl=60)
def get_inventory_data():
    try:
        response = requests.get(f"{API_BASE_URL}/inventory")
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            st.error(f"API Error: {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return pd.DataFrame()

def add_product(product_data):
    try:
        response = requests.post(f"{API_BASE_URL}/inventory", json=product_data)
        return response.status_code == 201
    except requests.exceptions.RequestException:
        return False

def update_product(product_id, product_data):
    try:
        response = requests.put(f"{API_BASE_URL}/inventory/{product_id}", json=product_data)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def delete_product(product_id):
    try:
        response = requests.delete(f"{API_BASE_URL}/inventory/{product_id}")
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="inventory-header">
    <h1>📦 Inventory Management</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem;">Smart Stock Management & Tracking System</p>
</div>
""", unsafe_allow_html=True)

# Backend status check
if not check_backend_health():
    st.error("❌ Backend disconnected. Please try again later.")
    st.stop()

# Load data from backend
inventory_df = get_inventory_data()

if inventory_df.empty:
    st.error("Unable to load inventory data. Please check backend connection.")
    st.stop()

# Sidebar backend status
st.sidebar.markdown("### 🔌 Backend Status")
if check_backend_health():
    st.sidebar.success("✅ Connected")
else:
    st.sidebar.error("❌ Disconnected")

# Sidebar filters
st.sidebar.markdown("### 🎛️ Filters")
categories = ['All'] + sorted(inventory_df['category'].unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

statuses = ['All'] + sorted(inventory_df['status'].unique().tolist())
selected_status = st.sidebar.selectbox("Status", statuses)

# Apply filters
filtered_df = inventory_df.copy()
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['category'] == selected_category]
if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['status'] == selected_status]

# Key metrics
st.markdown("### 📊 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Products", len(filtered_df))

with col2:
    low_stock = len(filtered_df[filtered_df['current_stock'] <= filtered_df['min_stock_level']])
    st.metric("Low Stock Items", low_stock)

with col3:
    out_of_stock = len(filtered_df[filtered_df['current_stock'] == 0])
    st.metric("Out of Stock", out_of_stock)

with col4:
    total_value = (filtered_df['current_stock'] * filtered_df['unit_price']).sum()
    st.metric("Total Inventory Value", f"${total_value:,.2f}")

# Alerts section
st.markdown("### 🚨 Inventory Alerts")
col1, col2 = st.columns(2)

with col1:
    low_stock_items = filtered_df[filtered_df['current_stock'] <= filtered_df['min_stock_level']]
    if len(low_stock_items) > 0:
        st.markdown("#### ⚠️ Low Stock Alerts")
        for _, item in low_stock_items.head(5).iterrows():
            st.markdown(f"""
            <div class="alert-card">
                <strong>{item['product_name']}</strong><br>
                Current: {item['current_stock']} | Min: {item['min_stock_level']}
            </div>
            """, unsafe_allow_html=True)

with col2:
    out_of_stock_items = filtered_df[filtered_df['current_stock'] == 0]
    if len(out_of_stock_items) > 0:
        st.markdown("#### ❌ Out of Stock")
        for _, item in out_of_stock_items.head(5).iterrows():
            st.markdown(f"""
            <div class="alert-card">
                <strong>{item['product_name']}</strong><br>
                Category: {item['category']} | Supplier: {item['supplier']}
            </div>
            """, unsafe_allow_html=True)

# Charts section
st.markdown("### 📈 Inventory Analytics")
col1, col2 = st.columns(2)

with col1:
    category_stock = filtered_df.groupby('category')['current_stock'].sum().reset_index()
    fig_pie = px.pie(category_stock, values='current_stock', names='category', title='Stock Distribution by Category')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    status_counts = filtered_df['status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_bar = px.bar(status_counts, x='Status', y='Count', title='Products by Status')
    st.plotly_chart(fig_bar, use_container_width=True)

# Product management actions
st.markdown("### 🔧 Product Management")

tab1, tab2, tab3 = st.tabs(["Add Product", "Update Product", "Delete Product"])

with tab1:
    with st.form("add_product"):
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name")
            category = st.selectbox("Category", inventory_df['category'].unique())
            current_stock = st.number_input("Current Stock", min_value=0, value=0)
        with col2:
            unit_price = st.number_input("Unit Price", min_value=0.0, value=0.0)
            min_stock = st.number_input("Min Stock Level", min_value=0, value=10)
            supplier = st.text_input("Supplier")
        
        if st.form_submit_button("Add Product"):
            product_data = {
                "product_name": product_name,
                "category": category,
                "current_stock": current_stock,
                "unit_price": unit_price,
                "min_stock_level": min_stock,
                "supplier": supplier
            }
            if add_product(product_data):
                st.success("Product added successfully!")
                st.rerun()
            else:
                st.error("Failed to add product")

with tab2:
    selected_product = st.selectbox("Select Product to Update", inventory_df['product_id'].tolist())
    if selected_product:
        product_info = inventory_df[inventory_df['product_id'] == selected_product].iloc[0]
        with st.form("update_product"):
            col1, col2 = st.columns(2)
            with col1:
                new_stock = st.number_input("New Stock Level", value=int(product_info['current_stock']))
                new_price = st.number_input("New Price", value=float(product_info['unit_price']))
            with col2:
                new_min_stock = st.number_input("New Min Stock", value=int(product_info['min_stock_level']))
                new_supplier = st.text_input("New Supplier", value=product_info['supplier'])
            
            if st.form_submit_button("Update Product"):
                update_data = {
                    "current_stock": new_stock,
                    "unit_price": new_price,
                    "min_stock_level": new_min_stock,
                    "supplier": new_supplier
                }
                if update_product(selected_product, update_data):
                    st.success("Product updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update product")

with tab3:
    delete_product_id = st.selectbox("Select Product to Delete", inventory_df['product_id'].tolist())
    if st.button("Delete Product", type="secondary"):
        if delete_product(delete_product_id):
            st.success("Product deleted successfully!")
            st.rerun()
        else:
            st.error("Failed to delete product")

# Detailed inventory table
st.markdown("### 📋 Detailed Inventory")
search_term = st.text_input("🔍 Search products...", placeholder="Enter product name or ID")

if search_term:
    filtered_df = filtered_df[
        filtered_df['product_name'].str.contains(search_term, case=False) |
        filtered_df['product_id'].str.contains(search_term, case=False)
    ]

st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Auto-refresh
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>📦 Inventory Management System | Real-time Stock Tracking</p>
</div>
""", unsafe_allow_html=True)