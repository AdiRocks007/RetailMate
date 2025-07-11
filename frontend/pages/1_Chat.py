import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime
import json

# Page configuration
st.set_page_config(page_title="RetailMate Chat", layout="wide")

# Custom CSS for chat interface
st.markdown("""
<style>
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        height: 500px;
        overflow-y: auto;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 5px 15px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px 15px 15px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .system-message {
        background: #f8f9fa;
        color: #6c757d;
        padding: 0.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #dee2e6;
        font-size: 0.9rem;
    }
    
    .quick-action {
        background: linear-gradient(135deg, #2ed573 0%, #17a2b8 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        display: inline-block;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #2ed573;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .customer-info {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    padding: 0.8rem 2.2rem;   /* Slightly more padding */
    font-weight: bold;
    transition: all 0.3s ease;
    width: 180px;
    height: 65px;             /* Increased height */
    white-space: normal;      /* Allow wrapping */
    font-size: 1rem;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Welcome to RetailMate! I'm your AI assistant ready to help you with any questions about our products and services. How can I assist you today?", "timestamp": datetime.now()}
    ]

if 'customer_info' not in st.session_state:
    st.session_state.customer_info = {
        "name": "John Doe",
        "email": "john.doe@email.com",
        "membership": "Premium",
        "orders": 23,
        "satisfaction": 4.8
    }

# Header
st.markdown("""
<div class="chat-header">
    <h1>💬 Chat with RetailMate</h1>
    <p style="font-size: 1.1rem; margin-top: 1rem;"><span class="status-indicator"></span>AI Assistant is Online</p>
</div>
""", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([3, 1])

with col1:
    # Chat interface
    st.markdown("### 💬 Chat Interface")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong> {message["content"]}<br>
                    <small>{message["timestamp"].strftime("%H:%M")}</small>
                </div>
                """, unsafe_allow_html=True)
            elif message["role"] == "assistant":
                st.markdown(f"""
                <div class="bot-message">
                    <strong>🤖 RetailMate:</strong> {message["content"]}<br>
                    <small>{message["timestamp"].strftime("%H:%M")}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="system-message">
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("### ✍ Send Message")
    
    # Quick action buttons
    st.markdown("*Quick Actions:*")
    
    col1_1, col1_2, col1_3, col1_4 = st.columns(4)
    
    with col1_1:
        if st.button("Product Info"):
            user_message = "I need information about your products"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            
            # Simulate AI response
            ai_response = "I'd be happy to help you with product information! We have a wide range of products including Electronics, Clothing, Home & Garden, Sports equipment, Books, and Beauty products. What specific category or product are you interested in?"
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now()})
            st.rerun()
    
    with col1_2:
        if st.button("Order Status"):
            user_message = "What's the status of my recent order?"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            
            ai_response = "Let me check your order status. Your most recent order #ORD-12345 was shipped yesterday and is currently in transit. Expected delivery is tomorrow by 3 PM. You can track it using the link sent to your email."
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now()})
            st.rerun()
    
    with col1_3:
        if st.button("Returns & Refunds"):
            user_message = "I need help with returns and refunds"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            
            ai_response = "I can help you with returns and refunds! We have a 30-day return policy for most items. As a Premium member, you also get free return shipping. Would you like to start a return for a specific item or do you need information about our refund process?"
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now()})
            st.rerun()
    
    with col1_4:
        if st.button("Recommendations"):
            user_message = "Can you recommend some products for me?"
            st.session_state.messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
            
            ai_response = "Based on your purchase history and preferences, I recommend: 1) New iPhone 15 Pro (Electronics) - 20% off for Premium members, 2) Nike Air Max sneakers (Sports) - trending among similar customers, 3) The latest bestseller novels (Books) - based on your reading history. Would you like detailed information about any of these?"
            st.session_state.messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now()})
            st.rerun()
    
    # Text input for custom messages
    user_input = st.text_input("Type your message here...", key="user_input", placeholder="Ask me anything about our products or services!")
    
    if st.button("Send Message") and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input, "timestamp": datetime.now()})
        
        # Simulate AI response based on input
        ai_responses = {
            "price": "Our prices are competitive and we offer regular discounts. Premium members get additional 10% off on all purchases. What specific product pricing are you interested in?",
            "delivery": "We offer multiple delivery options: Standard (3-5 days), Express (1-2 days), and Same-day delivery in select areas. Premium members get free standard shipping on all orders.",
            "quality": "Quality is our top priority. All our products go through rigorous quality checks and we offer warranties on eligible items. We also have a satisfaction guarantee - if you're not happy, we'll make it right!",
            "support": "Our customer support team is available 24/7 through chat, email, and phone. As a Premium member, you get priority support with average response time of under 2 minutes.",
            "account": "I can help you with account-related queries. You can update your profile, view order history, manage payment methods, and track your membership benefits through your account dashboard."
        }
        
        # Simple keyword matching for AI response
        response = "Thank you for your message! I understand you're asking about '{}'. Our customer service team will provide you with detailed information. Is there anything specific you'd like to know more about?".format(user_input.lower())
        
        for keyword, ai_response in ai_responses.items():
            if keyword in user_input.lower():
                response = ai_response
                break
        
        # Add AI response
        st.session_state.messages.append({"role": "assistant", "content": response, "timestamp": datetime.now()})
        st.rerun()

with col2:
    # Customer information sidebar
    st.markdown("### 👤 Customer Profile")
    
    st.markdown(f"""
    <div class="customer-info">
        <h4>🌟 {st.session_state.customer_info['name']}</h4>
        <p><strong>Email:</strong> {st.session_state.customer_info['email']}</p>
        <p><strong>Membership:</strong> {st.session_state.customer_info['membership']}</p>
        <p><strong>Total Orders:</strong> {st.session_state.customer_info['orders']}</p>
        <p><strong>Satisfaction:</strong> {st.session_state.customer_info['satisfaction']}/5.0 ⭐</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat statistics
    st.markdown("### 📊 Chat Statistics")
    
    total_messages = len([msg for msg in st.session_state.messages if msg["role"] in ["user", "assistant"]])
    user_messages = len([msg for msg in st.session_state.messages if msg["role"] == "user"])
    bot_messages = len([msg for msg in st.session_state.messages if msg["role"] == "assistant"])
    
    st.metric("Total Messages", total_messages)
    st.metric("Your Messages", user_messages)
    st.metric("AI Responses", bot_messages)
    
    # Satisfaction rating
    st.markdown("### ⭐ Rate This Chat")
    rating = st.slider("How satisfied are you with this chat?", 1, 5, 5)
    if st.button("Submit Rating"):
        st.success(f"Thank you for rating this chat {rating}/5 stars!")
    
    # Quick help
    st.markdown("### 🆘 Quick Help")
    st.info("""
    *Common Questions:*
    - Product information
    - Order status & tracking
    - Returns & refunds
    - Payment methods
    - Shipping options
    - Account management
    """)
    
    # Contact options
    st.markdown("### 📞 Other Contact Options")
    
    if st.button("📧 Email Support"):
        st.info("Email: support@retailmate.com\nResponse time: 2-4 hours")
    
    if st.button("📱 Call Us"):
        st.info("Phone: 1-800-RETAIL\nAvailable 24/7")
    
    if st.button("💬 Live Agent"):
        st.info("Connecting you to a human agent...\nEstimated wait time: 3 minutes")

# Clear chat button
if st.button("🗑 Clear Chat History"):
    st.session_state.messages = [
        {"role": "system", "content": "Chat history cleared. Welcome back to RetailMate! How can I assist you today?", "timestamp": datetime.now()}
    ]
    st.rerun()

# Chat analytics
st.markdown("### 📈 Chat Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Response Time", "< 2 sec", delta="Fast")

with col2:
    st.metric("Resolution Rate", "94%", delta="2% increase")

with col3:
    st.metric("Customer Satisfaction", "4.8/5", delta="0.1 improvement")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666;">
    <p>💬 RetailMate AI Chat | Available 24/7 | Powered by Advanced AI</p>
    <p>For urgent matters, please call our hotline: 1-800-RETAIL</p>
</div>
""", unsafe_allow_html=True)