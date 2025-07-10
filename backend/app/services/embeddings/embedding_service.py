"""
Embedding Service for RetailMate
Generates vector embeddings for semantic search
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
from ...models.unified_models.product_models import UnifiedProduct, ProductCollection
from ...models.unified_models.user_models import UnifiedUser, UserCollection

logger = logging.getLogger("retailmate-embeddings")

class EmbeddingService:
    """Service for generating and managing embeddings"""
    # Cache loaded SentenceTransformer to avoid reloading for each instance
    _model_instance: Optional[SentenceTransformer] = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.embeddings_dir = Path("backend/app/data/embeddings")
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    def load_model(self):
        """Load the sentence transformer model"""
        # Use a shared model instance to improve performance
        if EmbeddingService._model_instance is None:
            try:
                logger.info(f"Loading sentence transformer model: {self.model_name}")
                EmbeddingService._model_instance = SentenceTransformer(self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                raise
        # Assign the cached model to this instance
        self.model = EmbeddingService._model_instance
    
    def generate_product_embeddings(self, products: List[UnifiedProduct]) -> Dict[str, np.ndarray]:
        """Generate embeddings for products"""
        self.load_model()
        
        try:
            # Prepare texts for embedding
            texts = []
            product_ids = []
            
            for product in products:
                texts.append(product.embedding_text)
                product_ids.append(product.id)
            
            logger.info(f"Generating embeddings for {len(texts)} products")
            
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # Create mapping
            embedding_dict = {}
            for i, product_id in enumerate(product_ids):
                embedding_dict[product_id] = embeddings[i]
            
            logger.info(f"Generated {len(embedding_dict)} product embeddings")
            return embedding_dict
            
        except Exception as e:
            logger.error(f"Error generating product embeddings: {e}")
            raise
    
    def generate_user_embeddings(self, users: List[UnifiedUser]) -> Dict[str, np.ndarray]:
        """Generate embeddings for user preferences"""
        self.load_model()
        
        try:
            # Prepare texts for embedding
            texts = []
            user_ids = []
            
            for user in users:
                texts.append(user.preference_text)
                user_ids.append(user.id)
            
            logger.info(f"Generating embeddings for {len(texts)} users")
            
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=True)
            
            # Create mapping
            embedding_dict = {}
            for i, user_id in enumerate(user_ids):
                embedding_dict[user_id] = embeddings[i]
            
            logger.info(f"Generated {len(embedding_dict)} user embeddings")
            return embedding_dict
            
        except Exception as e:
            logger.error(f"Error generating user embeddings: {e}")
            raise
    
    def save_embeddings(self, embeddings: Dict[str, np.ndarray], filename: str):
        """Save embeddings to disk"""
        try:
            filepath = self.embeddings_dir / f"{filename}.pkl"
            with open(filepath, 'wb') as f:
                pickle.dump(embeddings, f)
            
            logger.info(f"Saved {len(embeddings)} embeddings to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            raise
    
    def load_embeddings(self, filename: str) -> Optional[Dict[str, np.ndarray]]:
        """Load embeddings from disk"""
        try:
            filepath = self.embeddings_dir / f"{filename}.pkl"
            
            if not filepath.exists():
                logger.warning(f"Embeddings file not found: {filepath}")
                return None
            
            with open(filepath, 'rb') as f:
                embeddings = pickle.load(f)
            
            logger.info(f"Loaded {len(embeddings)} embeddings from {filepath}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return None
    
    def find_similar_products(self, query_text: str, product_embeddings: Dict[str, np.ndarray], 
                            top_k: int = 5) -> List[Dict[str, Any]]:
        """Find similar products using semantic search"""
        self.load_model()
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query_text])[0]
            
            # Calculate similarities
            similarities = []
            for product_id, embedding in product_embeddings.items():
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                similarities.append({
                    'product_id': product_id,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar products: {e}")
            return []
    
    def find_similar_users(self, target_user_id: str, user_embeddings: Dict[str, np.ndarray], 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """Find users with similar preferences"""
        try:
            if target_user_id not in user_embeddings:
                logger.warning(f"User {target_user_id} not found in embeddings")
                return []
            
            target_embedding = user_embeddings[target_user_id]
            
            # Calculate similarities
            similarities = []
            for user_id, embedding in user_embeddings.items():
                if user_id == target_user_id:
                    continue
                
                similarity = np.dot(target_embedding, embedding) / (
                    np.linalg.norm(target_embedding) * np.linalg.norm(embedding)
                )
                similarities.append({
                    'user_id': user_id,
                    'similarity': float(similarity)
                })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        if not self.model:
            try:
                self.load_model()
            except Exception as e:
                return {"status": "error", "error": str(e)}
        if not self.model:
            return {"status": "not_loaded"}
        return {
            "model_name": self.model_name,
            "max_seq_length": getattr(self.model, 'max_seq_length', 'unknown'),
        }
