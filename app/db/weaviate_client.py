import weaviate
from typing import Dict, List, Any, Optional
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()

class WeaviateClient:
    def __init__(self):
        self.client = None
        self.class_name = settings.WEAVIATE_CLASS_NAME
        
    async def connect(self):
        """Initialize Weaviate connection"""
        try:
            auth_config = None
            if settings.WEAVIATE_API_KEY:
                auth_config = weaviate.AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
            
            self.client = weaviate.Client(
                url=settings.WEAVIATE_URL,
                auth_client_secret=auth_config,
                timeout_config=(5, 60)
            )
            
         
            if self.client.is_ready():
                logger.info("Successfully connected to Weaviate")
                await self._ensure_schema_exists()
            else:
                raise Exception("Weaviate is not ready")
                
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    async def _ensure_schema_exists(self):
        """Ensure the required schema exists"""
        try:
           
            if not self.client.schema.exists(self.class_name):
                logger.info(f"Creating Weaviate class: {self.class_name}")
                
                class_definition = {
                    "class": self.class_name,
                    "description": "ITSM knowledge documents",
                    "vectorizer": "none",  
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Document content"
                        },
                        {
                            "name": "source",
                            "dataType": ["string"],
                            "description": "Source URL"
                        },
                        {
                            "name": "category",
                            "dataType": ["string"],
                            "description": "Document category"
                        },
                        {
                            "name": "toolName",
                            "dataType": ["string"],
                            "description": "ITSM tool name"
                        },
                        {
                            "name": "section",
                            "dataType": ["string"],
                            "description": "Document section"
                        },
                        {
                            "name": "chunkIndex",
                            "dataType": ["int"],
                            "description": "Chunk index"
                        },
                        {
                            "name": "toolRank",
                            "dataType": ["int"],
                            "description": "Tool ranking"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["date"],
                            "description": "Creation timestamp"
                        }
                    ]
                }
                
                self.client.schema.create_class(class_definition)
                logger.info("Schema created successfully")
            else:
                logger.info("Schema already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring schema exists: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to Weaviate"""
        try:
            with self.client.batch as batch:
                batch.batch_size = 100
                
                for doc in documents:
                    
                    properties = {
                        "content": doc["content"],
                        "source": doc["source"],
                        "category": doc["category"],
                        "toolName": doc.get("tool_name", ""),
                        "section": doc.get("section", ""),
                        "chunkIndex": doc.get("chunk_index", 0),
                        "toolRank": doc.get("tool_rank", 0),
                        "timestamp": doc.get("timestamp", "")
                    }
                    
                   
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.class_name,
                        vector=doc.get("vector")
                    )
            
            logger.info(f"Added {len(documents)} documents to Weaviate")
            
        except Exception as e:
            logger.error(f"Error adding documents to Weaviate: {e}")
            raise
    
    async def search(self, 
                    query_vector: List[float], 
                    limit: int = 5,
                    where_filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Search documents by vector similarity"""
        try:
            query = (
                self.client.query
                .get(self.class_name, [
                    "content",
                    "source",
                    "category",
                    "toolName",
                    "section",
                    "chunkIndex",
                    "toolRank"
                ])
                .with_near_vector({"vector": query_vector})
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
            )
            
            if where_filter:
                query = query.with_where(where_filter)
            
            result = query.do()
            
            documents = []
            if "data" in result and "Get" in result["data"]:
                for item in result["data"]["Get"][self.class_name]:
                    documents.append({
                        "content": item["content"],
                        "source": item["source"],
                        "category": item["category"],
                        "tool_name": item["toolName"],
                        "section": item["section"],
                        "chunk_index": item["chunkIndex"],
                        "tool_rank": item["toolRank"],
                        "certainty": item["_additional"]["certainty"],
                        "distance": item["_additional"]["distance"]
                    })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def delete_all_documents(self):
        """Delete all documents from the class"""
        try:
            self.client.schema.delete_class(self.class_name)
            await self._ensure_schema_exists()
            logger.info("All documents deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    async def get_document_count(self) -> int:
        """Get total number of documents"""
        try:
            result = (
                self.client.query
                .aggregate(self.class_name)
                .with_meta_count()
                .do()
            )
            
            if "data" in result and "Aggregate" in result["data"]:
                return result["data"]["Aggregate"][self.class_name][0]["meta"]["count"]
            return 0
            
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def close(self):
        """Close Weaviate connection"""
        if self.client:
            self.client = None
            logger.info("Weaviate connection closed")


weaviate_client = WeaviateClient()
