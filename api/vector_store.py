"""
ITPF Legal Search - Pinecone Vector Storage System
نظام تخزين المتجهات باستخدام Pinecone
"""

import os
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pinecone import Pinecone, ServerlessSpec
import json

logger = logging.getLogger(__name__)

class PineconeLegalVectorStore:
    """مخزن المتجهات القانونية باستخدام Pinecone"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = "itpf-legal-search"
        self.dimension = 384  # For paraphrase-multilingual-MiniLM-L12-v2
        self.metric = "cosine"
        self.cloud = "aws"
        self.region = "us-east-1"
        self.api_key = None
        
    async def initialize_pinecone(self, api_key: str = None):
        """تهيئة اتصال Pinecone"""
        try:
            # Get API key from parameter or environment
            self.api_key = api_key or os.getenv("PINECONE_API_KEY")
            if not self.api_key:
                logger.warning("Pinecone API key not provided, using local vector storage")
                return False
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.api_key)
            logger.info("Pinecone client initialized successfully")
            
            # Check if index exists, create if not
            await self._ensure_index_exists()
            
            return True
            
        except Exception as e:
            logger.error(f"Pinecone initialization error: {e}")
            return False
    
    async def _ensure_index_exists(self):
        """التأكد من وجود الفهرس أو إنشاؤه"""
        try:
            # List existing indexes
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                # Create serverless index (2025 best practice)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region
                    )
                )
                
                # Wait for index to be ready
                logger.info("Waiting for index to be ready...")
                while not self.pc.describe_index(self.index_name).status['ready']:
                    await asyncio.sleep(1)
                
                logger.info("Index created and ready!")
            else:
                logger.info(f"Index {self.index_name} already exists")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info("Connected to Pinecone index successfully")
            
        except Exception as e:
            logger.error(f"Index setup error: {e}")
            raise
    
    async def store_embeddings(self, chunks: List[Dict[str, Any]], embeddings: np.ndarray, language: str):
        """تخزين المتجهات في Pinecone"""
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return False
                
            vectors_to_upsert = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create unique vector ID
                vector_id = f"{language}_{chunk['chunk_id']}_{i}"
                
                # Prepare metadata (Pinecone has metadata size limits)
                metadata = {
                    "language": language,
                    "type": chunk.get('type', 'unknown'),
                    "chunk_id": chunk['chunk_id'],
                    "title": chunk.get('title', '')[:500],  # Truncate to avoid size limits
                    "source": chunk.get('metadata', {}).get('source', 'unknown'),
                    "content_length": len(chunk.get('content', '')),
                    "created_at": int(time.time())
                }
                
                # Add type-specific metadata
                if chunk.get('type') == 'article':
                    metadata["article_number"] = chunk.get('article_number')
                    metadata["section"] = chunk.get('section', '')[:200]
                elif chunk.get('type') == 'appendix':
                    metadata["appendix_number"] = chunk.get('appendix_number')
                elif chunk.get('type') == 'appendix_section':
                    metadata["appendix_number"] = chunk.get('appendix_number')
                    metadata["section_name"] = chunk.get('section_name', '')[:200]
                
                # Store truncated content in metadata (Pinecone limit ~40KB per vector)
                content = chunk.get('content', '')
                if len(content) > 1000:  # Reasonable limit for metadata
                    metadata["content_preview"] = content[:1000] + "..."
                    metadata["content_truncated"] = True
                else:
                    metadata["content_preview"] = content
                    metadata["content_truncated"] = False
                
                vector_item = {
                    "id": vector_id,
                    "values": embedding.tolist(),
                    "metadata": metadata
                }
                
                vectors_to_upsert.append(vector_item)
            
            # Upsert vectors in batches (Pinecone recommends batch size of 100-1000)
            batch_size = 100
            total_vectors = len(vectors_to_upsert)
            
            logger.info(f"Upserting {total_vectors} vectors to Pinecone in batches of {batch_size}")
            
            for i in range(0, total_vectors, batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                
                try:
                    upsert_response = self.index.upsert(vectors=batch)
                    logger.info(f"Batch {i//batch_size + 1}: Upserted {upsert_response['upserted_count']} vectors")
                except Exception as e:
                    logger.error(f"Batch upsert error: {e}")
                    # Continue with other batches
                
                # Small delay between batches to avoid rate limits
                await asyncio.sleep(0.1)
            
            logger.info(f"Successfully stored {total_vectors} {language} vectors in Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Embedding storage error: {e}")
            return False
    
    async def semantic_search(self, query_embedding: np.ndarray, language: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """البحث الدلالي في Pinecone"""
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return []
            
            # Prepare query filters
            query_filter = {"language": language}
            if filters:
                query_filter.update(filters)
            
            # Perform vector search
            search_results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=query_filter
            )
            
            # Format results
            results = []
            for match in search_results.matches:
                result = {
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata,
                    "rank": len(results) + 1
                }
                
                # Extract key information from metadata
                metadata = match.metadata
                result.update({
                    "type": metadata.get('type', 'unknown'),
                    "chunk_id": metadata.get('chunk_id', ''),
                    "title": metadata.get('title', ''),
                    "content": metadata.get('content_preview', ''),
                    "content_truncated": metadata.get('content_truncated', False),
                    "source": metadata.get('source', 'unknown'),
                    "language": metadata.get('language', language)
                })
                
                # Add type-specific fields
                if metadata.get('type') == 'article':
                    result["article_number"] = metadata.get('article_number')
                    result["section"] = metadata.get('section', '')
                elif metadata.get('type') == 'appendix':
                    result["appendix_number"] = metadata.get('appendix_number')
                elif metadata.get('type') == 'appendix_section':
                    result["appendix_number"] = metadata.get('appendix_number')
                    result["section_name"] = metadata.get('section_name', '')
                
                results.append(result)
            
            logger.info(f"Pinecone search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Pinecone search error: {e}")
            return []
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """إحصائيات فهرس Pinecone"""
        try:
            if not self.index:
                return {"status": "not_initialized"}
            
            # Get index description
            index_desc = self.pc.describe_index(self.index_name)
            
            # Get index statistics
            index_stats = self.index.describe_index_stats()
            
            return {
                "status": "connected",
                "index_name": self.index_name,
                "dimension": index_desc.dimension,
                "metric": index_desc.metric,
                "total_vector_count": index_stats.total_vector_count,
                "index_fullness": index_stats.index_fullness,
                "namespaces": index_stats.namespaces,
                "spec": {
                    "cloud": index_desc.spec.serverless.cloud if hasattr(index_desc.spec, 'serverless') else 'unknown',
                    "region": index_desc.spec.serverless.region if hasattr(index_desc.spec, 'serverless') else 'unknown'
                },
                "ready": index_desc.status.ready
            }
            
        except Exception as e:
            logger.error(f"Index stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def hybrid_search(self, query_embedding: np.ndarray, keyword_filters: Dict[str, Any], language: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """بحث مختلط: دلالي + كلمات مفتاحية"""
        try:
            # Perform semantic search with keyword filters
            results = await self.semantic_search(
                query_embedding, 
                language, 
                top_k=top_k * 2,  # Get more results for filtering
                filters=keyword_filters
            )
            
            # Additional keyword filtering on content if needed
            if keyword_filters.get('content_keywords'):
                keywords = keyword_filters['content_keywords']
                filtered_results = []
                
                for result in results:
                    content = result.get('content', '').lower()
                    title = result.get('title', '').lower()
                    
                    # Check if any keyword matches
                    if any(keyword.lower() in content or keyword.lower() in title for keyword in keywords):
                        result['keyword_match'] = True
                        filtered_results.append(result)
                    elif len(filtered_results) < top_k:  # Include some semantic-only matches
                        result['keyword_match'] = False
                        filtered_results.append(result)
                
                results = filtered_results[:top_k]
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return []
    
    async def delete_all_vectors(self, language: str = None):
        """حذف جميع المتجهات (للتجديد)"""
        try:
            if not self.index:
                logger.error("Pinecone index not initialized")
                return False
            
            if language:
                # Delete vectors for specific language
                self.index.delete(filter={"language": language})
                logger.info(f"Deleted all {language} vectors from Pinecone")
            else:
                # Delete all vectors
                self.index.delete(delete_all=True)
                logger.info("Deleted all vectors from Pinecone")
            
            return True
            
        except Exception as e:
            logger.error(f"Vector deletion error: {e}")
            return False

# Global instance
pinecone_store = PineconeLegalVectorStore()