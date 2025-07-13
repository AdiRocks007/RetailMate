"""
Comprehensive RetailMate System Test Suite
Tests all components: Data, Embeddings, RAG, Calendar, and MCP Tools
"""

import asyncio
import sys
import json
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

class RetailMateTestSuite:
    def __init__(self):
        self.test_results = {}
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["-u", "-m", "backend.app.mcp.server"],
        )
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting RetailMate Comprehensive Test Suite...")
        
        async with stdio_client(self.server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # Test 1: Data Normalization
                await self.test_data_normalization(session)
                
                # Test 2: Embedding Generation
                await self.test_embedding_generation(session)
                
                # Test 3: Vector Store Initialization
                await self.test_vector_store_setup(session)
                
                # Test 4: Basic Product Search
                await self.test_basic_search(session)
                
                # Test 5: User-Personalized Search
                await self.test_personalized_search(session)
                
                # Test 6: Calendar Integration
                await self.test_calendar_integration(session)
                
                # Test 7: Event-Based Shopping
                await self.test_event_shopping(session)
                
                # Test 8: Category-Based Filtering
                await self.test_category_filtering(session)
                
                # Test 9: Multi-Context RAG Search
                await self.test_advanced_rag(session)
                
                # Test 10: System Performance
                await self.test_system_performance(session)
                
                # Generate Test Report
                self.generate_test_report()
    
    async def test_data_normalization(self, session):
        """Test data normalization from APIs"""
        print("\n📊 Test 1: Data Normalization...")
        
        try:
            result = await session.call_tool("normalize_all_data", {"include_embeddings": False})
            response = json.loads(result.content[0].text)
            
            self.test_results["data_normalization"] = {
                "status": "✅ PASS" if response["status"] == "success" else "❌ FAIL",
                "products_normalized": response["products"]["total_count"],
                "users_normalized": response["users"]["total_count"],
                "categories_found": len(response["products"]["category_breakdown"])
            }
            
            print(f"   Products: {response['products']['total_count']}")
            print(f"   Users: {response['users']['total_count']}")
            print(f"   Categories: {len(response['products']['category_breakdown'])}")
            
        except Exception as e:
            self.test_results["data_normalization"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_embedding_generation(self, session):
        """Test embedding generation for products and users"""
        print("\n🧠 Test 2: Embedding Generation...")
        
        try:
            result = await session.call_tool("generate_embeddings", {"target": "both"})
            response = json.loads(result.content[0].text)
            
            self.test_results["embedding_generation"] = {
                "status": "✅ PASS" if response["status"] == "success" else "❌ FAIL",
                "products_embedded": response["embeddings_generated"].get("products", 0),
                "users_embedded": response["embeddings_generated"].get("users", 0),
                "model_info": response.get("model_info", {})
            }
            
            print(f"   Product embeddings: {response['embeddings_generated'].get('products', 0)}")
            print(f"   User embeddings: {response['embeddings_generated'].get('users', 0)}")
            
        except Exception as e:
            self.test_results["embedding_generation"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_vector_store_setup(self, session):
        """Test ChromaDB vector store initialization"""
        print("\n🗄️ Test 3: Vector Store Setup...")
        
        try:
            result = await session.call_tool("initialize_vector_store", {"reset_existing": True})
            response = json.loads(result.content[0].text)
            
            self.test_results["vector_store"] = {
                "status": "✅ PASS" if response["status"] == "success" else "❌ FAIL",
                "products_in_store": response["products_added"],
                "users_in_store": response["users_added"],
                "collection_stats": response["collection_stats"]
            }
            
            print(f"   Products in ChromaDB: {response['products_added']}")
            print(f"   Users in ChromaDB: {response['users_added']}")
            
        except Exception as e:
            self.test_results["vector_store"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_basic_search(self, session):
        """Test basic semantic search functionality"""
        print("\n🔍 Test 4: Basic Product Search...")
        
        test_queries = [
            "smartphone for photography",
            "comfortable running shoes",
            "kitchen appliances for cooking",
            "elegant jewelry for special occasions"
        ]
        
        search_results = {}
        
        for query in test_queries:
            try:
                result = await session.call_tool("semantic_search", {"query": query, "top_k": 3})
                response = json.loads(result.content[0].text)
                
                search_results[query] = {
                    "products_found": len(response["results"]),
                    "top_similarity": response["results"][0]["similarity"] if response["results"] else 0
                }
                
            except Exception as e:
                search_results[query] = {"error": str(e)}
        
        self.test_results["basic_search"] = {
            "status": "✅ PASS" if all("error" not in result for result in search_results.values()) else "❌ FAIL",
            "queries_tested": len(test_queries),
            "results": search_results
        }
        
        print(f"   Tested {len(test_queries)} queries")
        for query, result in search_results.items():
            if "error" not in result:
                print(f"   '{query}': {result['products_found']} products (similarity: {result['top_similarity']:.3f})")
    
    async def test_personalized_search(self, session):
        """Test user-personalized search"""
        print("\n👤 Test 5: Personalized Search...")
        
        try:
            result = await session.call_tool("rag_search", {
                "query": "I need something stylish for a special occasion",
                "user_id": "dummyjson_1",
                "max_results": 5
            })
            response = json.loads(result.content[0].text)
            
            self.test_results["personalized_search"] = {
                "status": "✅ PASS" if response["context_summary"]["products_found"] > 0 else "❌ FAIL",
                "products_found": response["context_summary"]["products_found"],
                "user_context_available": response["context_summary"]["user_context_available"],
                "calendar_events": response["context_summary"]["calendar_events"]
            }
            
            print(f"   Products found: {response['context_summary']['products_found']}")
            print(f"   User context: {response['context_summary']['user_context_available']}")
            print(f"   Calendar events: {response['context_summary']['calendar_events']}")
            
        except Exception as e:
            self.test_results["personalized_search"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_calendar_integration(self, session):
        """Test calendar event integration"""
        print("\n📅 Test 6: Calendar Integration...")
        
        try:
            result = await session.call_tool("get_calendar_events", {"days_ahead": 14})
            response = json.loads(result.content[0].text)
            
            self.test_results["calendar_integration"] = {
                "status": "✅ PASS" if response["total_events"] > 0 else "❌ FAIL",
                "total_events": response["total_events"],
                "shopping_events": len([e for e in response["events"] if e.get("shopping_context")]),
                "next_urgent_event": response.get("next_urgent_event", {}).get("title", "None")
            }
            
            print(f"   Total events: {response['total_events']}")
            print(f"   Shopping events: {len([e for e in response['events'] if e.get('shopping_context')])}")
            print(f"   Next urgent: {response.get('next_urgent_event', {}).get('title', 'None')}")
            
        except Exception as e:
            self.test_results["calendar_integration"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_event_shopping(self, session):
        """Test event-based shopping suggestions"""
        print("\n🎉 Test 7: Event-Based Shopping...")
        
        try:
            # First get an event ID
            events_result = await session.call_tool("get_calendar_events", {"days_ahead": 14})
            events_response = json.loads(events_result.content[0].text)
            
            if events_response["events"]:
                event_id = events_response["events"][0]["id"]
                
                result = await session.call_tool("event_shopping_assistant", {"event_id": event_id})
                response = json.loads(result.content[0].text)
                
                self.test_results["event_shopping"] = {
                    "status": "✅ PASS" if "event_details" in response else "❌ FAIL",
                    "event_title": response.get("event_details", {}).get("title", "Unknown"),
                    "recommended_products": len(response.get("recommended_products", [])),
                    "shopping_urgency": response.get("shopping_urgency", "unknown")
                }
                
                print(f"   Event: {response.get('event_details', {}).get('title', 'Unknown')}")
                print(f"   Products recommended: {len(response.get('recommended_products', []))}")
                print(f"   Urgency: {response.get('shopping_urgency', 'unknown')}")
            else:
                self.test_results["event_shopping"] = {"status": "⚠️ SKIP", "reason": "No events found"}
                
        except Exception as e:
            self.test_results["event_shopping"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_category_filtering(self, session):
        """Test category-based product filtering"""
        print("\n🏷️ Test 8: Category Filtering...")
        
        try:
            # Get available categories
            categories_result = await session.call_tool("get_all_categories", {})
            categories_response = json.loads(categories_result.content[0].text)
            
            test_categories = categories_response.get("all_unique_categories", [])[:3]
            category_results = {}
            
            for category in test_categories:
                try:
                    result = await session.call_tool("get_enhanced_products", {
                        "category": category,
                        "limit": 5
                    })
                    response = json.loads(result.content[0].text)
                    category_results[category] = len(response.get("products", []))
                except:
                    category_results[category] = 0
            
            self.test_results["category_filtering"] = {
                "status": "✅ PASS" if sum(category_results.values()) > 0 else "❌ FAIL",
                "categories_tested": len(test_categories),
                "category_results": category_results
            }
            
            print(f"   Categories tested: {len(test_categories)}")
            for cat, count in category_results.items():
                print(f"   {cat}: {count} products")
                
        except Exception as e:
            self.test_results["category_filtering"] = {"status": "❌ FAIL", "error": str(e)}
    
    async def test_advanced_rag(self, session):
        """Test advanced RAG with multiple contexts"""
        print("\n🧠 Test 9: Advanced RAG Search...")
        
        complex_queries = [
            "I have a business meeting next week and need professional attire",
            "Looking for gifts for a family celebration happening soon",
            "Need cooking equipment for preparing holiday meals"
        ]
        
        rag_results = {}
        
        for query in complex_queries:
            try:
                result = await session.call_tool("rag_search", {
                    "query": query,
                    "user_id": "dummyjson_1",
                    "max_results": 3
                })
                response = json.loads(result.content[0].text)
                
                rag_results[query] = {
                    "products_found": response["context_summary"]["products_found"],
                    "context_available": response["context_summary"]["user_context_available"],
                    "calendar_integration": response["context_summary"]["calendar_events"] > 0
                }
                
            except Exception as e:
                rag_results[query] = {"error": str(e)}
        
        self.test_results["advanced_rag"] = {
            "status": "✅ PASS" if all("error" not in result for result in rag_results.values()) else "❌ FAIL",
            "complex_queries_tested": len(complex_queries),
            "results": rag_results
        }
        
        print(f"   Complex queries tested: {len(complex_queries)}")
        for query, result in rag_results.items():
            if "error" not in result:
                print(f"   Products: {result['products_found']}, Context: {result['context_available']}")
    
    async def test_system_performance(self, session):
        """Test system performance metrics"""
        print("\n⚡ Test 10: System Performance...")
        
        try:
            import time
            
            # Test response times
            start_time = time.time()
            await session.call_tool("get_vector_store_stats", {})
            stats_time = time.time() - start_time
            
            start_time = time.time()
            await session.call_tool("semantic_search", {"query": "test", "top_k": 5})
            search_time = time.time() - start_time
            
            start_time = time.time()
            await session.call_tool("rag_search", {"query": "test query", "max_results": 3})
            rag_time = time.time() - start_time
            
            self.test_results["performance"] = {
                "status": "✅ PASS" if all(t < 10 for t in [stats_time, search_time, rag_time]) else "❌ FAIL",
                "stats_response_time": f"{stats_time:.2f}s",
                "search_response_time": f"{search_time:.2f}s",
                "rag_response_time": f"{rag_time:.2f}s"
            }
            
            print(f"   Stats query: {stats_time:.2f}s")
            print(f"   Search query: {search_time:.2f}s")
            print(f"   RAG query: {rag_time:.2f}s")
            
        except Exception as e:
            self.test_results["performance"] = {"status": "❌ FAIL", "error": str(e)}
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📋 RETAILMATE COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "✅ PASS")
        failed_tests = sum(1 for result in self.test_results.values() if result["status"] == "❌ FAIL")
        skipped_tests = sum(1 for result in self.test_results.values() if result["status"].startswith("⚠️"))
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Skipped: {skipped_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            print(f"   {test_name}: {result['status']}")
            if "error" in result:
                print(f"      Error: {result['error']}")
        
        print(f"\n🎯 SYSTEM CAPABILITIES VERIFIED:")
        if self.test_results.get("data_normalization", {}).get("status") == "✅ PASS":
            print("   ✅ Multi-API data integration and normalization")
        if self.test_results.get("embedding_generation", {}).get("status") == "✅ PASS":
            print("   ✅ Semantic embedding generation")
        if self.test_results.get("vector_store", {}).get("status") == "✅ PASS":
            print("   ✅ ChromaDB vector storage")
        if self.test_results.get("personalized_search", {}).get("status") == "✅ PASS":
            print("   ✅ User-personalized recommendations")
        if self.test_results.get("calendar_integration", {}).get("status") == "✅ PASS":
            print("   ✅ Calendar-aware shopping suggestions")
        if self.test_results.get("advanced_rag", {}).get("status") == "✅ PASS":
            print("   ✅ Multi-context RAG system")

async def main():
    test_suite = RetailMateTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
