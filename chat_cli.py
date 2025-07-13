#!/usr/bin/env python3
"""RetailMate Chat CLI for testing AI flows: shopping, cart, event, and conversation."""
import argparse
import asyncio
import json
import uuid

from backend.app.services.ai.ollama.ollama_service import OllamaService
from backend.app.services.api_clients.calendar_apis.calendar_client import CalendarClient
from backend.app.services.cart.cart_service import CartService

async def main():
    parser = argparse.ArgumentParser(description="RetailMate Chat CLI")
    subparsers = parser.add_subparsers(dest="command")

    shopping_parser = subparsers.add_parser("shopping", help="Generate shopping recommendation")
    shopping_parser.add_argument("query", help="User shopping query")
    shopping_parser.add_argument("--user-id", help="User ID for personalization", default=None)

    cart_parser = subparsers.add_parser("cart", help="Generate cart-aware shopping recommendation")
    cart_parser.add_argument("query", help="User shopping query")
    cart_parser.add_argument("--user-id", help="User ID for cart context", default=None)

    event_parser = subparsers.add_parser("event", help="Generate event shopping advice")
    event_parser.add_argument("event_id", help="Event ID to generate plan for")

    chat_parser = subparsers.add_parser("chat", help="Chat conversation")
    chat_parser.add_argument("message", help="Message to chat")
    chat_parser.add_argument("--conversation-id", dest="conversation_id", help="Conversation ID", required=True)
    chat_parser.add_argument("--user-id", help="User ID", default=None)

    args = parser.parse_args()

    service = OllamaService()
    calendar_client = CalendarClient()
    cart_service = CartService()

    # autonomous interactive chat when no subcommand is provided
    if not args.command:
        # Track last recommendations for 'add it' shortcuts
        last_recommendations = []
        conversation_id = str(uuid.uuid4())
        user_id = args.user_id if hasattr(args, "user_id") else None
        print(f"Starting autonomous interactive session (ID: {conversation_id}). Type 'exit' or 'quit' to exit.")
        # Show upcoming events
        events = await calendar_client.get_upcoming_events()
        if events:
            print("Upcoming events in the next 30 days:")
            for e in events:
                print(f"- {e['id']}: {e['title']} on {e['start_date']} ({e['days_until']} days away)")
        while True:
            message = input("You: ")
            if message.strip().lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            # Handle 'add it' to cart for last recommendations
            lower_msg = message.strip().lower()
            if lower_msg.startswith("add it") or lower_msg.startswith("add this"):
                if last_recommendations:
                    prod = last_recommendations[0]
                    pid = prod.get("id") or prod.get("product_id")
                    resp = await cart_service.add_item(user_id or "default", pid, 1)
                    print(resp.get("message") or resp.get("error"))
                    summary = await cart_service.get_cart_summary(user_id or "default")
                    print(json.dumps(summary, indent=2))
                else:
                    print("No recent recommendations to add.")
                continue
            # AI-driven interpretation of the user message
            interpretation = await service.interpret_and_act(message, conversation_id, user_id)
            # Ensure interpretation is a dict
            if not isinstance(interpretation, dict):
                interpretation = {}
            reply = interpretation.get("reply")
            # Safely get action, default to empty dict if missing or None
            action = interpretation.get("action") or {}
            if reply:
                print(reply)
            action_type = action.get("type")
            if action_type == "add_to_cart":
                product_id = action.get("product_id")
                quantity = action.get("quantity", 1)
                resp = await cart_service.add_item(user_id or "default", product_id, quantity)
                print(resp.get("message") or resp.get("error"))
                summary = await cart_service.get_cart_summary(user_id or "default")
                print(json.dumps(summary, indent=2))
            elif action_type == "remove_from_cart":
                product_id = action.get("product_id")
                quantity = action.get("quantity")
                resp = await cart_service.remove_item(user_id or "default", product_id, quantity)
                print(resp.get("message") or resp.get("error"))
                summary = await cart_service.get_cart_summary(user_id or "default")
                print(json.dumps(summary, indent=2))
            elif action_type == "show_cart":
                summary = await cart_service.get_cart_contents(user_id or "default")
                print(json.dumps(summary, indent=2))
            elif action_type == "list_events":
                events = await calendar_client.get_upcoming_events()
                if events:
                    print("Upcoming events in the next 30 days:")
                    for e in events:
                        print(f"- {e['id']}: {e['title']} on {e['start_date']} ({e['days_until']} days away)")
                else:
                    print("No upcoming events found.")
            elif action_type == "suggest_for_event":
                event_id = action.get("event_id")
                # Use AI event shopping advice to provide chat response
                advice = await service.generate_event_shopping_advice(event_id)
                # Print AI-formatted advice
                print(f"RetailMate: {advice.get('ai_advice')}")
                # Show recommended products
                if advice.get('recommended_products'):
                    print("Recommendations:")
                    for p in advice['recommended_products']:
                        pid = p.get('id') or p.get('product_id', '')
                        price = p.get('price', '')
                        print(f"- {p.get('title')} (ID: {pid}): ${price}")
                # Debug JSON
                print(json.dumps(advice, indent=2))
                continue
            elif action_type == "next_event":
                # next_event reply already printed; skip fallback
                continue
            elif action_type == "clarify":
                # clarification question already printed as reply
                pass
            elif action_type == "none":
                # Use AI conversation to get chat reply and product suggestions
                result = await service.chat_conversation(message, conversation_id, user_id)
                # Track last recommendations
                last_recommendations = result.get("context_products", [])
                print(f"RetailMate: {result['ai_response']}")
                if result.get("context_products"):
                    print("Recommendations:")
                    for p in result["context_products"]:
                        print(f"- {p['title']} (ID: {p['product_id'] if p.get('product_id') else p.get('id', p.get('title'))}): ${p.get('price')}")
                # Debug JSON
                print(json.dumps(interpretation, indent=2))
            elif action_type == "search":
                # Direct shopping recommendation based on query
                search_query = action.get("query", message)
                result = await service.generate_shopping_recommendation(search_query, user_id)
                # Track last recommendations
                last_recommendations = result.get("recommended_products", [])
                # Show AI's descriptive response
                print(f"RetailMate: {result['ai_response']}")
                # Display structured recommendations
                if result.get("recommended_products"):
                    print("Recommendations:")
                    for p in result["recommended_products"]:
                        pid = p.get("id") or p.get("product_id") or ""
                        print(f"- {p['title']} (ID: {pid}): ${p.get('price')}")
                # Debug JSON
                print(json.dumps(interpretation, indent=2))
            # Continue loop
            continue
        return

    if args.command == "shopping":
        result = await service.generate_shopping_recommendation(args.query, args.user_id)
    elif args.command == "cart":
        result = await service.generate_cart_aware_recommendation(args.query, args.user_id)
    elif args.command == "event":
        result = await service.generate_event_shopping_advice(args.event_id)
    elif args.command == "chat":
        result = await service.chat_conversation(args.message, args.conversation_id, args.user_id)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main()) 