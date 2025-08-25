import streamlit as st
import asyncio
from frontend.components import get_products
from backend.app.services.cart.cart_service import CartService
from backend.app.services.api_clients.calendar_apis.calendar_client import CalendarClient
from backend.app.services.ai.ollama.ollama_service import OllamaService

st.set_page_config(page_title="RetailMate", page_icon="🛍", layout="wide", initial_sidebar_state="expanded")

st.title("🛍 RetailMate")
st.caption("Minimalistic shopping, cart, and event planning")

# Initialize services and user context
cart_service = CartService()
calendar_client = CalendarClient()
ai_service = OllamaService()
user_id = "default"

tabs = st.tabs(["Shop", "Cart", "Events"])

with tabs[0]:
    st.subheader("🛍 Shop")
    products = get_products(limit=12)
    # Grid view: 4 columns
    grid_cols = st.columns(4, gap="small")
    for idx, product in enumerate(products):
        col = grid_cols[idx % 4]
        with col:
            # Card style
            st.image(product.get('thumbnail', ''), use_column_width=True)
            st.markdown(f"### {product['title']}")
            st.markdown(f"**${product['price']:.2f}**")
            if st.button("Add to Cart", key=f"add_{product['id']}"):
                asyncio.run(cart_service.add_item(user_id, product['id'], 1))
                try:
                    st.toast(f"Added '{product['title']}' to cart 🛒")
                except AttributeError:
                    st.success(f"Added '{product['title']}' to cart 🛒")
                st.experimental_rerun()

with tabs[1]:
    st.subheader("🛒 Your Cart")
    cart_data = asyncio.run(cart_service.get_cart_contents(user_id))
    cart_items = cart_data.get('items', [])
    if not cart_items:
        st.info("Your cart is empty.")
    else:
        # Table layout
        for item in cart_items:
            cols = st.columns([1, 3, 1, 1])
            with cols[0]:
                img_url = item.get('image') or item.get('thumbnail') or ""
                if img_url:
                    st.image(img_url, width=80)
            with cols[1]:
                st.markdown(f"**{item['title']}**")
                st.write(f"Quantity: {item['quantity']}")
            with cols[2]:
                st.write(f"${item['price']*item['quantity']:.2f}")
            with cols[3]:
                if st.button("Remove", key=f"rm_{item['product_id']}"):
                    asyncio.run(cart_service.remove_item(user_id, item['product_id']))
                    st.experimental_rerun()
        st.markdown(f"**Total: ${cart_data.get('estimated_total',0.0):.2f}**")
        if st.button("Clear Cart"):
            asyncio.run(cart_service.clear_cart(user_id))
            st.experimental_rerun()

with tabs[2]:
    st.subheader("🎉 Event Planning")
    events = asyncio.run(calendar_client.get_upcoming_events())
    if not events:
        st.info("No upcoming events.")
    else:
        # Select event
        event_map = {e['id']: e for e in events}
        event_list = [f"{e['title']} ({e['start_date']})" for e in events]
        choice = st.selectbox("Select an Event", event_list)
        # Map back to id
        selected_id = events[event_list.index(choice)]['id']
        if st.button("Get Suggestions", key="event_suggest"):
            advice = asyncio.run(ai_service.generate_event_shopping_advice(selected_id))
            # AI advice text
            st.markdown("### RetailMate Advice")
            st.write(advice.get('ai_advice',''))
            # Show recommended products
            recs = advice.get('recommended_products', [])
            if recs:
                st.markdown("#### Recommended Products")
                rec_cols = st.columns(3, gap="small")
                for i, p in enumerate(recs):
                    c = rec_cols[i % 3]
                    with c:
                        if p.get('thumbnail'):
                            st.image(p['thumbnail'], width=100)
                        st.markdown(f"**{p.get('title')}**")
                        st.write(f"${p.get('price')}")
                        if st.button("Add to Cart", key=f"ev_add_{p.get('id')}"):
                            asyncio.run(cart_service.add_item(user_id, p.get('id'), 1))
                            try:
                                st.toast(f"Added '{p.get('title')}' to cart 🛒")
                            except AttributeError:
                                st.success(f"Added '{p.get('title')}' to cart 🛒")
                            st.experimental_rerun()