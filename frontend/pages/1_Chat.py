import streamlit as st
import asyncio
import uuid
import json
from datetime import datetime
from backend.app.services.ai.ollama.ollama_service import OllamaService
from backend.app.services.cart.cart_service import CartService
from backend.app.services.api_clients.calendar_apis.calendar_client import CalendarClient

st.set_page_config(page_title="RetailMate Chat", layout="wide")

# Initialize services and session state
if 'service' not in st.session_state:
    st.session_state.service = OllamaService()
if 'cart_service' not in st.session_state:
    st.session_state.cart_service = CartService()
if 'calendar_client' not in st.session_state:
    st.session_state.calendar_client = CalendarClient()
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Welcome to RetailMate! How can I assist you today?", "timestamp": datetime.now()}
    ]
if 'cart_summary' not in st.session_state:
    st.session_state.cart_summary = {"empty": True, "total_items": 0, "estimated_total": 0.0}
if 'events' not in st.session_state:
    st.session_state.events = asyncio.run(st.session_state.calendar_client.get_upcoming_events())
# Add initialization for recent recommendations
if 'last_recommendations' not in st.session_state:
    st.session_state.last_recommendations = []

# Layout: two columns
col1, col2 = st.columns([3, 1])

with col1:
    st.header("💬 Chat")
    # Display chat messages
    for msg in st.session_state.messages:
        role = "You" if msg["role"] == "user" else ("RetailMate" if msg["role"] == "assistant" else "System")
        st.markdown(f"**{role}:** {msg['content']}")

    # Input box
    user_input = st.text_input("Message:", key="user_input")
    if st.button("Send") and user_input:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": datetime.now()})
        # Handle 'add it' shortcuts for recent recommendations
        lower_msg = user_input.strip().lower()
        if lower_msg.startswith("add it") or lower_msg.startswith("add this"):
            if not st.session_state.last_recommendations:
                st.session_state.messages.append({"role": "assistant", "content": "No recent recommendations to add.", "timestamp": datetime.now()})
            else:
                prod = st.session_state.last_recommendations[0]
                pid = prod.get("id") or prod.get("product_id")
                resp = asyncio.run(st.session_state.cart_service.add_item("default", pid, 1))
                msg = resp.get("message") or resp.get("error")
                st.session_state.messages.append({"role": "assistant", "content": msg, "timestamp": datetime.now()})
                st.session_state.cart_summary = resp.get("cart_summary", {})
            st.experimental_rerun()
        # Interpret and act
        interp = asyncio.run(
            st.session_state.service.interpret_and_act(
                user_input, st.session_state.conversation_id, None
            )
        )
        # Reply from AI
        reply = interp.get("reply")
        action = interp.get("action") or {}
        if reply:
            st.session_state.messages.append({"role": "assistant", "content": reply, "timestamp": datetime.now()})
        # Handle actions
        action_type = action.get("type")
        if action_type == "add_to_cart":
            pid = action.get("product_id")
            qty = action.get("quantity", 1)
            resp = asyncio.run(st.session_state.cart_service.add_item("default", pid, qty))
            msg = resp.get("message") or resp.get("error")
            st.session_state.messages.append({"role": "assistant", "content": msg, "timestamp": datetime.now()})
            st.session_state.cart_summary = resp.get("cart_summary", {})
        elif action_type == "remove_from_cart":
            pid = action.get("product_id")
            qty = action.get("quantity")
            resp = asyncio.run(st.session_state.cart_service.remove_item("default", pid, qty))
            msg = resp.get("message") or resp.get("error")
            st.session_state.messages.append({"role": "assistant", "content": msg, "timestamp": datetime.now()})
            st.session_state.cart_summary = resp.get("cart_summary", {})
        elif action_type == "show_cart":
            resp = asyncio.run(st.session_state.cart_service.get_cart_contents("default"))
            st.session_state.cart_summary = resp
            st.session_state.messages.append({"role": "assistant", "content": json.dumps(resp, indent=2), "timestamp": datetime.now()})
        elif action_type == "list_events":
            ev = asyncio.run(st.session_state.calendar_client.get_upcoming_events())
            st.session_state.events = ev
            text = "Upcoming events:\n" + "\n".join([f"- {e['title']} on {e['start_date']} ({e['days_until']} days away)" for e in ev])
            st.session_state.messages.append({"role": "assistant", "content": text, "timestamp": datetime.now()})
        elif action_type == "suggest_for_event":
            eid = action.get("event_id")
            advice = asyncio.run(st.session_state.service.generate_event_shopping_advice(eid))
            ai_advice = advice.get("ai_advice") or advice.get("reply")
            if ai_advice:
                st.session_state.messages.append({"role": "assistant", "content": ai_advice, "timestamp": datetime.now()})
            recs = advice.get("recommended_products", [])
            for p in recs:
                text = f"- {p.get('title')} (ID: {p.get('id') or p.get('product_id')}) : ${p.get('price')}"
                st.session_state.messages.append({"role": "assistant", "content": text, "timestamp": datetime.now()})
        elif action_type == "none":
            convo = asyncio.run(
                st.session_state.service.chat_conversation(
                    user_input, st.session_state.conversation_id, None
                )
            )
            resp_text = convo.get("ai_response") or convo.get("reply")
            if resp_text:
                st.session_state.messages.append({"role": "assistant", "content": resp_text, "timestamp": datetime.now()})
            st.session_state.last_recommendations = convo.get("context_products", [])
        elif action_type == "search":
            query = action.get("query", user_input)
            res = asyncio.run(st.session_state.service.generate_shopping_recommendation(query, None))
            ai_text = res.get("ai_response")
            if ai_text:
                st.session_state.messages.append({"role": "assistant", "content": ai_text, "timestamp": datetime.now()})
            recs = res.get("recommended_products", [])
            for p in recs:
                text = f"- {p.get('title')} (ID: {p.get('id') or p.get('product_id')}) : ${p.get('price')}"
                st.session_state.messages.append({"role": "assistant", "content": text, "timestamp": datetime.now()})
            st.session_state.last_recommendations = recs
        # Clear input and rerun
        st.experimental_rerun()

with col2:
    st.header("🛒 Cart Summary")
    st.json(st.session_state.cart_summary)
    st.header("📅 Upcoming Events")
    if st.session_state.events:
        for e in st.session_state.events:
            st.write(f"- {e['title']} on {e['start_date']} ({e['days_until']} days away)")
    else:
        st.write("No upcoming events.")