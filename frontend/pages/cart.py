import streamlit as st

st.set_page_config(page_title="Cart", page_icon="🛒", layout="wide")

if 'cart_items' not in st.session_state:
    st.session_state.cart_items = []

def cart_total():
    return sum(item['price'] * item['quantity'] for item in st.session_state.cart_items)

def cart_count():
    return sum(item['quantity'] for item in st.session_state.cart_items)

def update_quantity(idx, delta):
    st.session_state.cart_items[idx]['quantity'] += delta
    if st.session_state.cart_items[idx]['quantity'] < 1:
        st.session_state.cart_items[idx]['quantity'] = 1
    st.experimental_rerun()

def remove_item(idx):
    st.session_state.cart_items.pop(idx)
    st.experimental_rerun()

def clear_cart():
    st.session_state.cart_items = []
    st.experimental_rerun()

st.title("🛒 Your Cart")

if not st.session_state.cart_items:
    st.info("Your cart is empty.")
else:
    for idx, item in enumerate(st.session_state.cart_items):
        cols = st.columns([2, 1, 1, 1])
        with cols[0]:
            st.write(f"**{item['name']}**")
            st.write(f"${item['price']:.2f} x {item['quantity']}")
        with cols[1]:
            if st.button("-", key=f"dec_{idx}"):
                update_quantity(idx, -1)
            if st.button("+", key=f"inc_{idx}"):
                update_quantity(idx, 1)
        with cols[2]:
            st.write(f"${item['price']*item['quantity']:.2f}")
        with cols[3]:
            if st.button("Remove", key=f"rm_{idx}"):
                remove_item(idx)
    st.markdown(f"**Total:** ${cart_total():.2f}")
    if st.button("Clear Cart"):
        clear_cart()

st.markdown("---")
st.caption("RetailMate - Minimal Cart | Powered by MCP")