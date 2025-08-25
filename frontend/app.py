import streamlit as st
import asyncio
from frontend.components import get_products
from backend.app.services.cart.cart_service import CartService

st.set_page_config(page_title="RetailMate", page_icon="🛍", layout="wide")

st.title("🛍 RetailMate - Minimalistic Shop")

# Initialize CartService and load cart data for a default user
cart_service = CartService()
user_id = "default"
cart_data = asyncio.run(cart_service.get_cart_contents(user_id))
cart_items = cart_data.get("items", [])

# Layout: products on the left, cart on the right
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Products")
    products = get_products(limit=12)
    for product in products:
        if product.get('thumbnail'):
            st.image(product['thumbnail'], width=150)
        st.write(f"**{product['title']}**")
        st.write(f"${product['price']:.2f}")
        if st.button("Add to Cart", key=f"add_{product['id']}"):
            asyncio.run(cart_service.add_item(user_id, product['id'], 1))
            st.experimental_rerun()
        st.markdown("---")

with col2:
    st.subheader("Your Cart")
    if not cart_items:
        st.write("Cart is empty")
    else:
        total = 0.0
        for item in cart_items:
            line_total = item['price'] * item['quantity']
            st.write(f"{item['title']} x{item['quantity']} - ${line_total:.2f}")
            total += line_total
        st.write(f"**Total: ${total:.2f}**")