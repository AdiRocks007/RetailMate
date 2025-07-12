"""
ChromaDB Vector Store for RetailMate
Manages product and user embeddings for semantic search
"""

import os
# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import logging
import chromadb
import chromadb.telemetry.product.posthog as _posthog
# Silence telemetry errors
_posthog.capture = lambda *args, **kwargs: None
_posthog.install = lambda *args, **kwargs: None
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from chromadb.config import Settings
from ....models.unified_models.product_models import UnifiedProduct, ProductCollection
from ....models.unified_models.user_models import UnifiedUser, UserCollection

logger = logging.getLogger("retailmate-chroma")

class ChromaVectorStore:
    """ChromaDB integration for RetailMate vector storage"""
    
    def __init__(self, persist_directory: str = "backend\\app\\data\\chromadb"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Collection names
        self.products_collection_name = "retailmate_products"
        self.users_collection_name = "retailmate_users"
        self.events_collection_name = "retailmate_events"
        
        logger.info(f"ChromaDB initialized with persist directory: {self.persist_directory}")
    
    def get_or_create_products_collection(self):
        """Get or create products collection"""
        try:
            collection = self.client.get_or_create_collection(
                name=self.products_collection_name,
                metadata={
                    "description": "RetailMate product embeddings",
                    "type": "products"
                }
            )
            logger.info(f"Products collection ready: {collection.count()} items")
            return collection
        except Exception as e:
            logger.error(f"Error creating products collection: {e}")
            raise
    
    def get_or_create_users_collection(self):
        """Get or create users collection"""
        try:
            collection = self.client.get_or_create_collection(
                name=self.users_collection_name,
                metadata={
                    "description": "RetailMate user preference embeddings",
                    "type": "users"
                }
            )
            logger.info(f"Users collection ready: {collection.count()} items")
            return collection
        except Exception as e:
            logger.error(f"Error creating users collection: {e}")
            raise
    
    def add_products(self, products: List[UnifiedProduct], embeddings: Dict[str, np.ndarray]):
        """Add products with embeddings to ChromaDB"""
        try:
            collection = self.get_or_create_products_collection()
            
            # Prepare data for ChromaDB
            ids = []
            embeddings_list = []
            metadatas = []
            documents = []
            
            for product in products:
                if product.id in embeddings:
                    ids.append(product.id)
                    embeddings_list.append(embeddings[product.id].tolist())
                    documents.append(product.embedding_text)
                    
                    # Create metadata
                    metadata = {
                        "title": product.title,
                        "category": product.category,
                        "normalized_category": product.normalized_category.value,
                        "price": product.price,
                        "source_api": product.source_api,
                        "brand": product.brand or "unknown",
                        "in_stock": product.availability.in_stock if product.availability else True,
                        "rating": product.rating.average if product.rating else 0.0,
                        "tags": ",".join(product.tags) if product.tags else ""
                    }
                    metadatas.append(metadata)
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"Added {len(ids)} products to ChromaDB")
            return len(ids)
            
        except Exception as e:
            logger.error(f"Error adding products to ChromaDB: {e}")
            raise
    
    def add_users(self, users: List[UnifiedUser], embeddings: Dict[str, np.ndarray]):
        """Add users with embeddings to ChromaDB"""
        try:
            collection = self.get_or_create_users_collection()
            
            # Prepare data for ChromaDB
            ids = []
            embeddings_list = []
            metadatas = []
            documents = []
            
            for user in users:
                if user.id in embeddings:
                    ids.append(user.id)
                    embeddings_list.append(embeddings[user.id].tolist())
                    documents.append(user.preference_text)
                    
                    # Create metadata
                    metadata = {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "age": user.age or 0,
                        "gender": user.gender.value if user.gender else "unknown",
                        "budget_range": user.shopping_preferences.budget_range.value,
                        "shopping_style": user.shopping_preferences.shopping_style.value,
                        "source_api": user.source_api,
                        "preferred_categories": ",".join(user.shopping_preferences.preferred_categories),
                        "location": f"{user.location.city}, {user.location.country}" if user.location and user.location.city else "unknown"
                    }
                    metadatas.append(metadata)
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings_list,
                metadatas=metadatas,
                documents=documents
            )
            
            logger.info(f"Added {len(ids)} users to ChromaDB")
            return len(ids)
            
        except Exception as e:
            logger.error(f"Error adding users to ChromaDB: {e}")
            raise
    
    def search_products(self, query_embedding: np.ndarray, n_results: int = 5, 
                       filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search products using vector similarity"""
        try:
            collection = self.get_or_create_products_collection()
            
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                if filters.get("category"):
                    where_clause["normalized_category"] = filters["category"]
                if filters.get("max_price"):
                    where_clause["price"] = {"$lte": filters["max_price"]}
                if filters.get("min_rating"):
                    where_clause["rating"] = {"$gte": filters["min_rating"]}
                if filters.get("in_stock_only"):
                    where_clause["in_stock"] = True
            
            # Perform search
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )
            
            # Format results
            search_results = {
                "total_found": len(results["ids"][0]),
                "products": []
            }
            
            for i in range(len(results["ids"][0])):
                product_result = {
                    "id": results["ids"][0][i],
                    "title": results["metadatas"][0][i]["title"],
                    "category": results["metadatas"][0][i]["normalized_category"],
                    "price": results["metadatas"][0][i]["price"],
                    "brand": results["metadatas"][0][i]["brand"],
                    "rating": results["metadatas"][0][i]["rating"],
                    "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "metadata": results["metadatas"][0][i],
                    "description_snippet": results["documents"][0][i][:200] + "..."
                }
                search_results["products"].append(product_result)
            
            logger.info(f"Found {len(search_results['products'])} products for search")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise
    
    def search_similar_users(self, user_id: str, n_results: int = 5) -> Dict[str, Any]:
        """Find users with similar preferences"""
        try:
            collection = self.get_or_create_users_collection()
            
            # Get the target user's embedding
            target_user = collection.get(ids=[user_id], include=["embeddings", "metadatas"])
            
            if not target_user["ids"]:
                raise ValueError(f"User {user_id} not found in collection")
            
            target_embedding = target_user["embeddings"][0]
            
            # Search for similar users
            results = collection.query(
                query_embeddings=[target_embedding],
                n_results=n_results + 1,  # +1 because target user will be included
                include=["metadatas", "documents", "distances"]
            )
            
            # Filter out the target user
            similar_users = {
                "target_user_id": user_id,
                "similar_users": []
            }
            
            for i in range(len(results["ids"][0])):
                if results["ids"][0][i] != user_id:
                    user_result = {
                        "id": results["ids"][0][i],
                        "name": f"{results['metadatas'][0][i]['first_name']} {results['metadatas'][0][i]['last_name']}",
                        "age": results["metadatas"][0][i]["age"],
                        "budget_range": results["metadatas"][0][i]["budget_range"],
                        "similarity": 1 - results["distances"][0][i],
                        "preferred_categories": results["metadatas"][0][i]["preferred_categories"].split(","),
                        "location": results["metadatas"][0][i]["location"]
                    }
                    similar_users["similar_users"].append(user_result)
            
            # Limit to requested number
            similar_users["similar_users"] = similar_users["similar_users"][:n_results]
            
            logger.info(f"Found {len(similar_users['similar_users'])} similar users for {user_id}")
            return similar_users
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about all collections"""
        try:
            stats = {
                "collections": {},
                "total_embeddings": 0
            }
            
            # Products collection stats
            try:
                products_collection = self.get_or_create_products_collection()
                products_count = products_collection.count()
                stats["collections"]["products"] = {
                    "count": products_count,
                    "name": self.products_collection_name
                }
                stats["total_embeddings"] += products_count
            except:
                stats["collections"]["products"] = {"count": 0, "error": "Collection not accessible"}
            
            # Users collection stats
            try:
                users_collection = self.get_or_create_users_collection()
                users_count = users_collection.count()
                stats["collections"]["users"] = {
                    "count": users_count,
                    "name": self.users_collection_name
                }
                stats["total_embeddings"] += users_count
            except:
                stats["collections"]["users"] = {"count": 0, "error": "Collection not accessible"}
            
            # Database info
            stats["database_info"] = {
                "persist_directory": str(self.persist_directory),
                "client_type": type(self.client).__name__
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def reset_collections(self):
        """Reset all collections (use with caution)"""
        try:
            self.client.reset()
            logger.info("All collections reset")
        except Exception as e:
            logger.error(f"Error resetting collections: {e}")
            raise
