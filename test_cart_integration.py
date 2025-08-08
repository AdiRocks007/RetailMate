"""
Comprehensive Cart Integration Tests for RetailMate
"""

import asyncio
import sys
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_complete_cart_workflow():
    """Test complete cart workflow with AI integration"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🛒 Testing Complete Cart Workflow...")
            await session.initialize()
            
            test_user_id = "dummyjson_1"
            
            # Step 1: Check initial cart (should be empty)
            print("\n✅ Step 1: Check initial cart status")
            result = await session.call_tool("get_cart_contents", {"user_id": test_user_id})
            cart_data = json.loads(result.content[0].text)
            print(f"Initial cart: {cart_data.get('total_items', 0)} items")
            
            # Step 2: Get AI recommendation for laptops
            print("\n✅ Step 2: Get AI laptop recommendations")
            result = await session.call_tool("ai_shopping_assistant", {
                "query": "I need a laptop for programming",
                "user_id": test_user_id
            })
            ai_response = json.loads(result.content[0].text)
            print(f"AI recommended {len(ai_response['recommended_products'])} products")
            
            # Step 3: Add recommended laptop to cart
            if ai_response['recommended_products']:
                laptop = ai_response['recommended_products'][0]
                print(f"\n✅ Step 3: Adding {laptop['title']} to cart")
                result = await session.call_tool("add_to_cart", {
                    "product_id": laptop['id'],
                    "user_id": test_user_id,
                    "quantity": 1,
                    "ai_reasoning": "Perfect for programming work based on your requirements"
                })
                add_result = json.loads(result.content[0].text)
                print(f"Add result: {add_result.get('message', 'Unknown')}")
            
            # Step 4: Check cart contents
            print("\n✅ Step 4: Check updated cart contents")
            result = await session.call_tool("get_cart_contents", {"user_id": test_user_id})
            cart_data = json.loads(result.content[0].text)
            print(f"Cart now has: {cart_data.get('total_items', 0)} items")
            print(f"Cart value: ${cart_data.get('estimated_total', 0):.2f}")
            
            # Step 5: Get cart-aware recommendations for accessories
            print("\n✅ Step 5: Get cart-aware accessory recommendations")
            result = await session.call_tool("ai_shopping_assistant", {
                "query": "What accessories do I need for my laptop?",
                "user_id": test_user_id
            })
            accessory_response = json.loads(result.content[0].text)
            print(f"AI Response: {accessory_response['ai_response'][:200]}...")
            
            # Step 6: Get smart cart suggestions
            print("\n✅ Step 6: Get smart cart suggestions")
            result = await session.call_tool("get_cart_suggestions", {"user_id": test_user_id})
            suggestions = json.loads(result.content[0].text)
            if 'suggestions' in suggestions:
                complementary = suggestions['suggestions'].get('complementary_products', [])
                print(f"Found {len(complementary)} complementary product suggestions")
            
            # Step 7: Add an accessory to cart
            print("\n✅ Step 7: Add accessory to cart")
            result = await session.call_tool("add_to_cart", {
                "product_id": "dummyjson_79",  # Wireless mouse
                "user_id": test_user_id,
                "quantity": 1,
                "ai_reasoning": "Complements your laptop for better productivity"
            })
            add_result = json.loads(result.content[0].text)
            print(f"Accessory add result: {add_result.get('message', 'Unknown')}")
            
            # Step 8: Final cart check
            print("\n✅ Step 8: Final cart status")
            result = await session.call_tool("get_cart_contents", {"user_id": test_user_id})
            final_cart = json.loads(result.content[0].text)
            print(f"Final cart: {final_cart.get('total_items', 0)} items")
            print(f"Final value: ${final_cart.get('estimated_total', 0):.2f}")
            
            # Step 9: Test cart optimization
            print("\n✅ Step 9: Test cart optimization")
            result = await session.call_tool("get_cart_suggestions", {"user_id": test_user_id})
            optimization = json.loads(result.content[0].text)
            if 'suggestions' in optimization:
                cart_opt = optimization['suggestions'].get('cart_optimization', {})
                print(f"Cart optimization suggestions: {len(cart_opt.get('suggestions', []))}")
            
            # Step 10: Clear cart
            print("\n✅ Step 10: Clear cart")
            result = await session.call_tool("clear_cart", {"user_id": test_user_id})
            clear_result = json.loads(result.content[0].text)
            print(f"Clear result: {clear_result.get('message', 'Unknown')}")
            
            print("\n🎉 Cart workflow test completed successfully!")

async def test_cart_edge_cases():
    """Test cart edge cases and error handling"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("🧪 Testing Cart Edge Cases...")
            await session.initialize()
            
            test_user_id = "test_edge_user"
            
            # Test 1: Add non-existent product
            print("\n✅ Test 1: Add non-existent product")
            result = await session.call_tool("add_to_cart", {
                "product_id": "nonexistent_product",
                "user_id": test_user_id,
                "quantity": 1
            })
            error_result = json.loads(result.content[0].text)
            print(f"Expected error: {error_result.get('success', 'Unknown')}")
            
            # Test 2: Remove from empty cart
            print("\n✅ Test 2: Remove from empty cart")
            result = await session.call_tool("remove_from_cart", {
                "product_id": "any_product",
                "user_id": test_user_id
            })
            remove_result = json.loads(result.content[0].text)
            print(f"Remove from empty cart: {remove_result.get('success', 'Unknown')}")
            
            # Test 3: Get suggestions for empty cart
            print("\n✅ Test 3: Get suggestions for empty cart")
            result = await session.call_tool("get_cart_suggestions", {"user_id": test_user_id})
            suggestions = json.loads(result.content[0].text)
            print(f"Empty cart suggestions: {suggestions.get('message', 'Unknown')}")
            
            print("\n🎉 Edge case tests completed!")

async def test_cart_performance():
    """Test cart performance with multiple operations"""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-u", "-m", "backend.app.mcp.server"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("⚡ Testing Cart Performance...")
            await session.initialize()
            
            test_user_id = "performance_test_user"
            
            # Test multiple rapid cart operations
            import time
            
            start_time = time.time()
            
            # Add multiple items quickly
            for i in range(5):
                await session.call_tool("add_to_cart", {
                    "product_id": f"dummyjson_{80 + i}",
                    "user_id": test_user_id,
                    "quantity": 1
                })
            
            # Get cart contents
            await session.call_tool("get_cart_contents", {"user_id": test_user_id})
            
            # Get suggestions
            await session.call_tool("get_cart_suggestions", {"user_id": test_user_id})
            
            end_time = time.time()
            
            print(f"⚡ Performance test completed in {end_time - start_time:.2f} seconds")
            
            # Clean up
            await session.call_tool("clear_cart", {"user_id": test_user_id})

if __name__ == "__main__":
    print("🚀 Starting RetailMate Cart Integration Tests")
    
    asyncio.run(test_complete_cart_workflow())
    print("\n" + "="*50 + "\n")
    
    asyncio.run(test_cart_edge_cases())
    print("\n" + "="*50 + "\n")
    
    asyncio.run(test_cart_performance())
    
    print("\n✨ All cart tests completed!")
