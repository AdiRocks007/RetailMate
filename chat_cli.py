#!/usr/bin/env python3
"""RetailMate Chat CLI for testing AI flows: shopping, cart, event, and conversation."""
import argparse
import asyncio
import json
import uuid

from backend.app.services.ai.ollama.ollama_service import OllamaService

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

    # interactive chat when no subcommand is provided
    if not args.command:
        conversation_id = str(uuid.uuid4())
        print(f"Starting interactive chat session (ID: {conversation_id}). Type 'exit' or 'quit' to exit.")
        while True:
            message = input("You: ")
            if message.strip().lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            result = await service.chat_conversation(message, conversation_id)
            print(f"RetailMate: {result['ai_response']}")
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