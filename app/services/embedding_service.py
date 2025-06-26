from typing import List, Dict, Any
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.DEVICE
        
    async def initialize(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=settings.HF_CACHE_DIR,
                device=self.device
            )
            
          
            test_embedding = self.model.encode(["test"], convert_to_tensor=False)
            logger.info(f"Embedding model loaded successfully. Dimension: {len(test_embedding[0])}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    async def encode_texts(self, texts: List[str]) -> List[List[float]]:
        """Encode texts into embeddings (batchwise)"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            batch_size = 32
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.model.encode(
                    batch,
                    convert_to_tensor=False,
                    show_progress_bar=False,
                    batch_size=batch_size
                )
                all_embeddings.extend(embeddings.tolist())
            
            logger.info(f"Encoded {len(texts)} texts into embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise

    async def encode_texts_average(self, texts: List[str]) -> List[float]:
        """Encode a list of texts and return their normalized average embedding"""
        try:
            embeddings = await self.encode_texts(texts)

            if not embeddings:
                logger.warning("No embeddings generated, returning a zero vector.")
                return np.zeros(self.model.get_sentence_embedding_dimension()).tolist()

           
            simple_avg = np.mean(embeddings, axis=0)
            
            normalized_vector = simple_avg / np.linalg.norm(simple_avg)
            return normalized_vector.tolist()

        except Exception as e:
            logger.error(f"Error averaging and normalizing embeddings: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension()).tolist()
    
    async def encode_query(self, query: str) -> List[float]:
        """Encode a single query into embedding"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            embedding = self.model.encode([query], convert_to_tensor=False)[0]
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error encoding query: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the embedding service is ready"""
        return self.model is not None


embedding_service = EmbeddingService()
