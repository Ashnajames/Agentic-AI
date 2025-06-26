import time
from typing import List, Dict, Any, Optional
from app.db.weaviate_client import weaviate_client
from app.services.scraper_service import ScraperService
from app.services.processor_service import ProcessorService
from app.services.embedding_service import embedding_service
from app.services.generation_service import generation_service
from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()

class RAGService:
    def __init__(self):
        self.scraper = ScraperService()
        self.processor = ProcessorService()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all RAG components"""
        try:
            logger.info("Initializing RAG service...")
            
            
            await weaviate_client.connect()
            
           
            await embedding_service.initialize()
            
            
            await generation_service.initialize()
            
           
            doc_count = await weaviate_client.get_document_count()
            if doc_count == 0:
                logger.info("No documents found, loading initial data...")
                await self.refresh_knowledge_base()
            
            self.initialized = True
            logger.info("RAG service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def query(self, 
                   question: str, 
                   conversation_history: Optional[List[Dict[str, str]]] = None,
                   max_results: int = 5) -> Dict[str, Any]:
        """Process a query through the RAG pipeline"""
        if not self.initialized:
            raise RuntimeError("RAG service not initialized")
        
        start_time = time.time()
        
        try:
            
            query_embedding = await embedding_service.encode_query(question)
            
            
            documents = await weaviate_client.search(
                query_vector=query_embedding,
                limit=max_results
            )
            
            if not documents:
                return {
                    'response': "I couldn't find relevant information to answer your question. Please try rephrasing or ask about specific ITSM tools.",
                    'sources': [],
                    'confidence': 0.0,
                    'processing_time': time.time() - start_time
                }
            
            
            response_text = await generation_service.generate_response(
                query=question,
                context_documents=documents,
                conversation_history=conversation_history
            )
            
            
            sources = []
            for doc in documents:
                sources.append({
                    'source': doc['source'],
                    'category': doc['category'],
                    'tool_name': doc['tool_name'],
                    'certainty': doc['certainty'],
                    'distance': doc['distance']
                })
            
          
            confidence = sum(doc['certainty'] for doc in documents) / len(documents)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processed query in {processing_time:.2f}s with confidence {confidence:.3f}")
            
            return {
                'response': response_text,
                'sources': sources,
                'confidence': confidence,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'response': f"An error occurred while processing your request: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'processing_time': time.time() - start_time
            }
    
    async def refresh_knowledge_base(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Refresh the knowledge base with latest data"""
        start_time = time.time()
        
        try:
            logger.info("Starting knowledge base refresh...")
            
          
            scraped_data = await self.scraper.scrape_itsm_content()
            
            if not scraped_data:
                raise Exception("Failed to scrape content from website")
            
           
            documents = await self.processor.process_scraped_content(scraped_data)
            
            if not documents:
                raise Exception("No documents were processed from scraped content")
            
            
            texts = [doc['content'] for doc in documents]
            embeddings = await embedding_service.encode_texts(texts)
            
           
            for doc, embedding in zip(documents, embeddings):
                doc['vector'] = embedding
            
         
            if force_refresh:
                await weaviate_client.delete_all_documents()
            
            
            await weaviate_client.add_documents(documents)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Knowledge base refreshed successfully in {processing_time:.2f}s")
            
            return {
                'status': 'success',
                'message': 'Knowledge base updated successfully',
                'documents_processed': len(documents),
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error refreshing knowledge base: {e}")
            return {
                'status': 'error',
                'message': f"Failed to refresh knowledge base: {str(e)}",
                'documents_processed': 0,
                'processing_time': time.time() - start_time
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all RAG components"""
        try:
            doc_count = await weaviate_client.get_document_count()
            
            return {
                'status': 'healthy' if self.initialized else 'initializing',
                'weaviate_ready': weaviate_client.client is not None,
                'embedding_ready': embedding_service.is_ready(),
                'generation_ready': generation_service.is_ready(),
                'document_count': doc_count,
                'last_updated': None 
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': 'error',
                'weaviate_ready': False,
                'embedding_ready': False,
                'generation_ready': False,
                'document_count': 0,
                'last_updated': None
            }
    
    def is_ready(self) -> bool:
        """Check if RAG service is ready"""
        return (
            self.initialized and
            weaviate_client.client is not None and
            embedding_service.is_ready() and
            generation_service.is_ready()
        )

rag_service = RAGService()