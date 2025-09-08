"""
ITPF Legal Search - Embeddings and Semantic Search
معالجة النصوص القانونية وإنشاء التمثيل المتجه
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
import os
import pickle
from .vector_store import pinecone_store

logger = logging.getLogger(__name__)

class LegalEmbeddingsManager:
    """مدير التمثيل المتجه للنصوص القانونية"""
    
    def __init__(self):
        self.model = None
        self.arabic_embeddings = None
        self.english_embeddings = None
        self.arabic_chunks = None
        self.english_chunks = None
        self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"  # Supports Arabic and English
        self.use_pinecone = False
        self.pinecone_ready = False
        
    async def initialize_model(self, pinecone_api_key: str = None):
        """تهيئة نموذج التمثيل المتجه وPinecone"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Sentence transformer model loaded successfully")
            
            # Try to initialize Pinecone
            if pinecone_api_key or os.getenv("PINECONE_API_KEY"):
                logger.info("Initializing Pinecone vector store...")
                self.pinecone_ready = await pinecone_store.initialize_pinecone(pinecone_api_key)
                if self.pinecone_ready:
                    self.use_pinecone = True
                    logger.info("Pinecone vector store ready!")
                else:
                    logger.warning("Pinecone initialization failed, using local embeddings")
            else:
                logger.info("No Pinecone API key provided, using local embeddings only")
            
            return True
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
            return False
    
    def smart_chunk_legal_text(self, article: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
        """تقسيم ذكي للنصوص القانونية"""
        chunks = []
        
        # Main article chunk
        if article.get('content'):
            main_chunk = {
                'type': 'article',
                'article_number': article.get('article_number'),
                'title': article.get('title', ''),
                'section': article.get('section', ''),
                'content': article['content'],
                'language': language,
                'chunk_id': f"art_{article.get('article_number', 'unknown')}_{language}",
                'metadata': {
                    'source': 'article',
                    'length': len(article['content']),
                    'has_subsections': bool(article.get('subsections', []))
                }
            }
            chunks.append(main_chunk)
        
        # Subsection chunks (if any)
        if article.get('subsections'):
            for i, subsection in enumerate(article['subsections']):
                if isinstance(subsection, dict) and subsection.get('title'):
                    sub_chunk = {
                        'type': 'subsection',
                        'article_number': article.get('article_number'),
                        'parent_title': article.get('title', ''),
                        'title': subsection['title'],
                        'content': str(subsection.get('content', subsection.get('description', ''))),
                        'language': language,
                        'chunk_id': f"art_{article.get('article_number', 'unknown')}_sub_{i}_{language}",
                        'metadata': {
                            'source': 'subsection',
                            'parent_article': article.get('article_number'),
                            'subsection_index': i
                        }
                    }
                    if sub_chunk['content']:  # Only add if has content
                        chunks.append(sub_chunk)
        
        return chunks
    
    def smart_chunk_appendix(self, appendix: Dict[str, Any], language: str) -> List[Dict[str, Any]]:
        """تقسيم ذكي للملاحق"""
        chunks = []
        
        # Main appendix info
        main_chunk = {
            'type': 'appendix',
            'appendix_number': appendix.get('appendix_number'),
            'title': appendix.get('title', ''),
            'content': f"الملحق رقم {appendix.get('appendix_number')}: {appendix.get('title', '')}" if language == 'ar' else f"Appendix {appendix.get('appendix_number')}: {appendix.get('title', '')}",
            'language': language,
            'chunk_id': f"app_{appendix.get('appendix_number', 'unknown')}_{language}",
            'metadata': {
                'source': 'appendix',
                'appendix_number': appendix.get('appendix_number')
            }
        }
        chunks.append(main_chunk)
        
        # Process appendix content structure
        content = appendix.get('content', {})
        if isinstance(content, dict):
            # Day-by-day competition structure
            for day_key, day_content in content.items():
                if isinstance(day_content, dict) and day_content.get('title'):
                    day_chunk = {
                        'type': 'appendix_section',
                        'appendix_number': appendix.get('appendix_number'),
                        'section_name': day_key,
                        'title': day_content['title'],
                        'content': self._extract_day_content(day_content, language),
                        'language': language,
                        'chunk_id': f"app_{appendix.get('appendix_number', 'unknown')}_{day_key}_{language}",
                        'metadata': {
                            'source': 'appendix_section',
                            'appendix_number': appendix.get('appendix_number'),
                            'section_type': day_key
                        }
                    }
                    chunks.append(day_chunk)
        
        return chunks
    
    def _extract_day_content(self, day_content: Dict[str, Any], language: str) -> str:
        """استخراج محتوى اليوم من الملحق"""
        content_parts = []
        
        if day_content.get('title'):
            content_parts.append(day_content['title'])
            
        if day_content.get('total_score'):
            content_parts.append(day_content['total_score'])
            
        # Extract competitions
        if day_content.get('competitions'):
            for comp in day_content['competitions']:
                if isinstance(comp, dict):
                    if comp.get('competition'):
                        content_parts.append(f"المسابقة: {comp['competition']}" if language == 'ar' else f"Competition: {comp['competition']}")
                    
                    if comp.get('runs'):
                        for run in comp['runs']:
                            if isinstance(run, dict):
                                run_info = f"الشوط {run.get('run', '')}: وتد {run.get('peg_size', '')}, زمن {run.get('time', '')}" if language == 'ar' else f"Run {run.get('run', '')}: {run.get('peg_size', '')} peg, {run.get('time', '')} time"
                                content_parts.append(run_info)
                    elif comp.get('run'):
                        run_info = f"الشوط {comp.get('run', '')}: وتد {comp.get('peg_size', '')}, زمن {comp.get('time', '')}" if language == 'ar' else f"Run {comp.get('run', '')}: {comp.get('peg_size', '')} peg, {comp.get('time', '')} time"
                        content_parts.append(run_info)
        
        return ' | '.join(content_parts)
    
    async def create_embeddings(self, texts: Dict[str, Any], language: str) -> Tuple[List[Dict], np.ndarray]:
        """إنشاء التمثيل المتجه للنصوص"""
        try:
            if not self.model:
                await self.initialize_model()
                if not self.model:
                    raise Exception("Failed to initialize embeddings model")
            
            # Create chunks
            all_chunks = []
            
            # Process articles
            for article in texts.get('articles', []):
                chunks = self.smart_chunk_legal_text(article, language)
                all_chunks.extend(chunks)
            
            # Process appendices
            for appendix in texts.get('appendices', []):
                chunks = self.smart_chunk_appendix(appendix, language)
                all_chunks.extend(chunks)
            
            logger.info(f"Created {len(all_chunks)} chunks for {language} texts")
            
            # Extract text content for embedding
            texts_to_embed = []
            for chunk in all_chunks:
                # Combine title and content for better semantic understanding
                text_content = ""
                if chunk.get('title'):
                    text_content += chunk['title'] + " "
                if chunk.get('content'):
                    text_content += chunk['content']
                texts_to_embed.append(text_content.strip())
            
            # Create embeddings
            logger.info(f"Creating embeddings for {len(texts_to_embed)} texts...")
            embeddings = self.model.encode(texts_to_embed, show_progress_bar=True)
            
            logger.info(f"Created embeddings with shape: {embeddings.shape}")
            
            return all_chunks, embeddings
            
        except Exception as e:
            logger.error(f"Embeddings creation error: {e}")
            raise
    
    async def process_all_texts(self, arabic_texts: Dict[str, Any], english_texts: Dict[str, Any]):
        """معالجة جميع النصوص وإنشاء التمثيل المتجه"""
        try:
            logger.info("Starting embeddings processing for all texts...")
            
            # Process Arabic texts
            logger.info("Processing Arabic texts...")
            self.arabic_chunks, self.arabic_embeddings = await self.create_embeddings(arabic_texts, 'ar')
            
            # Store in Pinecone if available
            if self.use_pinecone and self.arabic_chunks and self.arabic_embeddings is not None:
                logger.info("Storing Arabic embeddings in Pinecone...")
                await pinecone_store.store_embeddings(self.arabic_chunks, self.arabic_embeddings, 'ar')
            
            # Process English texts  
            logger.info("Processing English texts...")
            self.english_chunks, self.english_embeddings = await self.create_embeddings(english_texts, 'en')
            
            # Store in Pinecone if available
            if self.use_pinecone and self.english_chunks and self.english_embeddings is not None:
                logger.info("Storing English embeddings in Pinecone...")
                await pinecone_store.store_embeddings(self.english_chunks, self.english_embeddings, 'en')
            
            logger.info(f"Embeddings processing complete!")
            logger.info(f"Arabic: {len(self.arabic_chunks)} chunks, {self.arabic_embeddings.shape}")
            logger.info(f"English: {len(self.english_chunks)} chunks, {self.english_embeddings.shape}")
            
            if self.use_pinecone:
                logger.info("Embeddings stored in Pinecone vector database")
            
            return True
            
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return False
    
    async def semantic_search(self, query: str, language: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """البحث الدلالي في النصوص"""
        try:
            if not self.model:
                raise Exception("Embeddings model not initialized")
            
            # Create query embedding
            query_embedding = self.model.encode([query])
            
            # Use Pinecone if available, otherwise fallback to local search
            if self.use_pinecone and self.pinecone_ready:
                logger.info("Using Pinecone for semantic search")
                results = await pinecone_store.semantic_search(
                    query_embedding[0], 
                    language, 
                    top_k
                )
                
                # Format results for consistency
                for result in results:
                    result['similarity_score'] = result.pop('score', 0)
                
                return results
            else:
                logger.info("Using local embeddings for semantic search")
                return await self._local_semantic_search(query_embedding, language, top_k)
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def _local_semantic_search(self, query_embedding: np.ndarray, language: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """البحث الدلالي المحلي (عندما لا يتوفر Pinecone)"""
        try:
            # Choose language-specific data
            if language == 'ar':
                chunks = self.arabic_chunks
                embeddings = self.arabic_embeddings
            else:
                chunks = self.english_chunks
                embeddings = self.english_embeddings
                
            if chunks is None or embeddings is None:
                raise Exception(f"No local embeddings available for language: {language}")
            
            # Compute similarity scores
            similarities = np.dot(embeddings, query_embedding.T).flatten()
            
            # Get top-k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                result = chunks[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                result['rank'] = len(results) + 1
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Local semantic search error: {e}")
            return []
    
    async def get_embeddings_stats(self) -> Dict[str, Any]:
        """إحصائيات التمثيل المتجه"""
        try:
            stats = {
                'model_name': self.model_name,
                'model_loaded': self.model is not None,
                'arabic_ready': self.arabic_embeddings is not None,
                'english_ready': self.english_embeddings is not None,
                'pinecone_enabled': self.use_pinecone,
                'pinecone_ready': self.pinecone_ready
            }
            
            if self.arabic_embeddings is not None:
                stats['arabic_chunks'] = len(self.arabic_chunks)
                stats['arabic_embedding_shape'] = self.arabic_embeddings.shape
                
            if self.english_embeddings is not None:
                stats['english_chunks'] = len(self.english_chunks)
                stats['english_embedding_shape'] = self.english_embeddings.shape
            
            # Add Pinecone stats if available
            if self.pinecone_ready:
                pinecone_stats = await pinecone_store.get_index_stats()
                stats['pinecone_stats'] = pinecone_stats
                
            return stats
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {'error': str(e)}

# Global instance
embeddings_manager = LegalEmbeddingsManager()