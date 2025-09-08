"""
ITPF Legal Search System - RAG Implementation
نظام البحث القانوني للاتحاد الدولي لالتقاط الأوتاد
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
from .embeddings import embeddings_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ITPF Legal Search System",
    description="نظام البحث القانوني للاتحاد الدولي لالتقاط الأوتاد",
    version="2.0.0"
)

class SearchQuery(BaseModel):
    query: str
    language: str = "ar"  # "ar" for Arabic, "en" for English
    max_results: int = 5
    search_type: str = "semantic"  # "semantic" or "keyword"

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    processing_time: float
    integrity_check: Dict[str, Any]

class LegalTextLoader:
    """محمل النصوص القانونية مع فحص السلامة"""
    
    def __init__(self):
        self.arabic_texts = None
        self.english_texts = None
        self.reference_arabic_size = 0
        self.reference_english_size = 0
        
    async def load_reference_files(self):
        """تحميل الملفات المرجعية للمقارنة"""
        try:
            # Determine base path (Vercel vs local)
            base_path = '/var/task' if os.path.exists('/var/task') else '.'
            
            # Arabic reference
            arabic_path = f'{base_path}/arabic.txt'
            with open(arabic_path, 'r', encoding='utf-8') as f:
                arabic_ref = f.read()
                self.reference_arabic_size = len(arabic_ref)
                logger.info(f"Arabic reference loaded: {self.reference_arabic_size} chars")
            
            # English reference  
            english_path = f'{base_path}/english.txt'
            with open(english_path, 'r', encoding='utf-8') as f:
                english_ref = f.read()
                self.reference_english_size = len(english_ref)
                logger.info(f"English reference loaded: {self.reference_english_size} chars")
                
            return True
        except Exception as e:
            logger.error(f"Reference files loading error: {e}")
            return False
    
    async def load_partitioned_data(self):
        """تحميل البيانات المقسمة مع فحص السلامة"""
        try:
            # Determine base path (Vercel vs local)
            base_path = '/var/task' if os.path.exists('/var/task') else '.'
            
            # Load Arabic parts
            arabic_articles = []
            arabic_appendices = []
            
            for part in [1, 2, 3]:
                with open(f'{base_path}/api/arabic_part{part}.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    arabic_articles.extend(data['articles'])
                    
                    # Check for appendices in part 3
                    if part == 3 and 'appendices' in data:
                        arabic_appendices.extend(data['appendices'])
            
            # Load English parts
            english_articles = []
            english_appendices = []
            
            for part in [1, 2, 3]:
                with open(f'{base_path}/api/english_part{part}.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    english_articles.extend(data['articles'])
                    
                    # Check for appendices in part 3
                    if part == 3 and 'appendices' in data:
                        english_appendices.extend(data['appendices'])
            
            self.arabic_texts = {
                'articles': arabic_articles,
                'appendices': arabic_appendices
            }
            
            self.english_texts = {
                'articles': english_articles, 
                'appendices': english_appendices
            }
            
            # Integrity check
            integrity = await self.verify_integrity()
            logger.info(f"Data loaded. Integrity: {integrity}")
            
            return integrity['status'] == 'complete'
            
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return False
    
    async def verify_integrity(self):
        """فحص سلامة النصوص مقابل الملفات المرجعية"""
        try:
            # Count Arabic articles and appendices
            arabic_articles_count = len(self.arabic_texts['articles'])
            arabic_appendices_count = len(self.arabic_texts['appendices'])
            
            # Count English articles and appendices  
            english_articles_count = len(self.english_texts['articles'])
            english_appendices_count = len(self.english_texts['appendices'])
            
            # Check article numbers range (100-154)
            arabic_numbers = [art['article_number'] for art in self.arabic_texts['articles']]
            english_numbers = [art['article_number'] for art in self.english_texts['articles']]
            
            expected_numbers = set(range(100, 155))  # 100-154
            arabic_set = set(arabic_numbers)
            english_set = set(english_numbers)
            
            integrity = {
                'status': 'complete',
                'arabic_articles': arabic_articles_count,
                'english_articles': english_articles_count,
                'arabic_appendices': arabic_appendices_count,
                'english_appendices': english_appendices_count,
                'missing_arabic': list(expected_numbers - arabic_set),
                'missing_english': list(expected_numbers - english_set),
                'total_content_chars': {
                    'arabic': sum(len(art.get('content', '')) for art in self.arabic_texts['articles']),
                    'english': sum(len(art.get('content', '')) for art in self.english_texts['articles'])
                }
            }
            
            # Check completeness
            if (arabic_articles_count != 55 or english_articles_count != 55 or 
                arabic_appendices_count < 2 or english_appendices_count < 2 or
                len(integrity['missing_arabic']) > 0 or len(integrity['missing_english']) > 0):
                integrity['status'] = 'incomplete'
                integrity['errors'] = []
                
                if arabic_articles_count != 55:
                    integrity['errors'].append(f"Arabic articles: expected 55, got {arabic_articles_count}")
                if english_articles_count != 55:
                    integrity['errors'].append(f"English articles: expected 55, got {english_articles_count}")
                if arabic_appendices_count < 2:
                    integrity['errors'].append(f"Arabic appendices: expected 2, got {arabic_appendices_count}")
                if english_appendices_count < 2:
                    integrity['errors'].append(f"English appendices: expected 2, got {english_appendices_count}")
            
            return integrity
            
        except Exception as e:
            logger.error(f"Integrity verification error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Initialize loader
text_loader = LegalTextLoader()

@app.on_event("startup")
async def startup_event():
    """تحميل البيانات عند بدء التشغيل"""
    logger.info("Starting ITPF Legal Search System...")
    
    # Load reference files first
    ref_loaded = await text_loader.load_reference_files()
    if not ref_loaded:
        logger.error("Failed to load reference files")
        
    # Load partitioned data
    data_loaded = await text_loader.load_partitioned_data()
    if not data_loaded:
        logger.error("Failed to load partitioned data")
        return
    
    # Initialize embeddings
    logger.info("Initializing embeddings system...")
    embeddings_ready = await embeddings_manager.process_all_texts(
        text_loader.arabic_texts, 
        text_loader.english_texts
    )
    
    if embeddings_ready:
        logger.info("ITPF Legal Search System fully ready with semantic search!")
    else:
        logger.warning("System ready with keyword search only (embeddings failed)")

@app.get("/api/health")
async def health_check():
    """فحص حالة النظام"""
    if text_loader.arabic_texts is None or text_loader.english_texts is None:
        raise HTTPException(status_code=503, detail="System not ready")
    
    integrity = await text_loader.verify_integrity()
    
    return {
        "status": "healthy",
        "system": "ITPF Legal Search RAG System",
        "version": "2.0.0",
        "integrity": integrity,
        "timestamp": "2025-01-08"
    }

@app.post("/api/search")
async def search_legal_texts(query: SearchQuery):
    """البحث في النصوص القانونية"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Verify integrity first
        integrity = await text_loader.verify_integrity()
        if integrity['status'] != 'complete':
            raise HTTPException(status_code=503, detail="Text integrity check failed")
        
        results = []
        
        # Choose search method
        if query.search_type == "semantic" and embeddings_manager.model is not None:
            # Semantic search using embeddings
            logger.info(f"Performing semantic search for: {query.query}")
            semantic_results = await embeddings_manager.semantic_search(
                query.query, 
                query.language, 
                query.max_results
            )
            
            for result in semantic_results:
                formatted_result = {
                    "type": result.get('type', 'unknown'),
                    "title": result.get('title', ''),
                    "content": result.get('content', '')[:800] + "..." if len(result.get('content', '')) > 800 else result.get('content', ''),
                    "similarity_score": result.get('similarity_score', 0),
                    "rank": result.get('rank', 0),
                    "source": result.get('metadata', {}).get('source', 'unknown'),
                    "chunk_id": result.get('chunk_id', ''),
                    "search_method": "semantic"
                }
                
                # Add specific fields based on type
                if result.get('type') == 'article':
                    formatted_result["article_number"] = result.get('article_number')
                    formatted_result["section"] = result.get('section', '')
                elif result.get('type') == 'appendix':
                    formatted_result["appendix_number"] = result.get('appendix_number')
                elif result.get('type') == 'appendix_section':
                    formatted_result["appendix_number"] = result.get('appendix_number')
                    formatted_result["section_name"] = result.get('section_name', '')
                
                results.append(formatted_result)
        else:
            # Fallback to keyword search
            logger.info(f"Performing keyword search for: {query.query}")
            query_lower = query.query.lower()
            
            # Choose language texts
            texts = text_loader.arabic_texts if query.language == "ar" else text_loader.english_texts
            
            # Search in articles
            for article in texts['articles']:
                content = article.get('content', '').lower()
                title = article.get('title', '').lower()
                
                if query_lower in content or query_lower in title:
                    results.append({
                        "article_number": article['article_number'],
                        "title": article.get('title', ''),
                        "content": article.get('content', '')[:800] + "..." if len(article.get('content', '')) > 800 else article.get('content', ''),
                        "section": article.get('section', ''),
                        "relevance_score": 0.8,
                        "source": "article",
                        "type": "article",
                        "search_method": "keyword"
                    })
            
            # Search in appendices
            for appendix in texts['appendices']:
                content_str = str(appendix.get('content', '')).lower()
                title = appendix.get('title', '').lower()
                
                if query_lower in content_str or query_lower in title:
                    results.append({
                        "appendix_number": appendix['appendix_number'],
                        "title": appendix.get('title', ''),
                        "content": str(appendix.get('content', ''))[:800] + "...",
                        "relevance_score": 0.9,
                        "source": "appendix",
                        "type": "appendix",
                        "search_method": "keyword"
                    })
            
            # Sort by relevance and limit results
            results = sorted(results, key=lambda x: x.get('relevance_score', x.get('similarity_score', 0)), reverse=True)[:query.max_results]
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return SearchResponse(
            query=query.query,
            results=results,
            total_found=len(results),
            processing_time=round(processing_time, 3),
            integrity_check=integrity
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/article/{article_number}")
async def get_article(article_number: int, language: str = "ar"):
    """الحصول على مادة قانونية محددة"""
    try:
        texts = text_loader.arabic_texts if language == "ar" else text_loader.english_texts
        
        for article in texts['articles']:
            if article['article_number'] == article_number:
                return article
        
        raise HTTPException(status_code=404, detail=f"Article {article_number} not found")
        
    except Exception as e:
        logger.error(f"Article retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_system_stats():
    """إحصائيات النظام"""
    try:
        integrity = await text_loader.verify_integrity()
        embeddings_stats = await embeddings_manager.get_embeddings_stats()
        
        return {
            "system": "ITPF Legal Search System",
            "version": "2.0.0",
            "statistics": {
                "arabic_articles": len(text_loader.arabic_texts['articles']),
                "english_articles": len(text_loader.english_texts['articles']),
                "arabic_appendices": len(text_loader.arabic_texts['appendices']),
                "english_appendices": len(text_loader.english_texts['appendices']),
                "total_content_size": integrity.get('total_content_chars', {})
            },
            "integrity": integrity,
            "reference_sizes": {
                "arabic": text_loader.reference_arabic_size,
                "english": text_loader.reference_english_size
            },
            "embeddings": embeddings_stats,
            "capabilities": {
                "semantic_search": embeddings_stats.get('model_loaded', False),
                "keyword_search": True,
                "multilingual": True,
                "real_time_integrity_check": True
            }
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/embeddings/status")
async def get_embeddings_status():
    """حالة نظام التمثيل المتجه"""
    try:
        return await embeddings_manager.get_embeddings_stats()
    except Exception as e:
        logger.error(f"Embeddings status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search/hybrid")
async def hybrid_search(query: SearchQuery):
    """البحث المختلط: دلالي + كلمات مفتاحية"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Verify integrity first
        integrity = await text_loader.verify_integrity()
        if integrity['status'] != 'complete':
            raise HTTPException(status_code=503, detail="Text integrity check failed")
        
        if not (embeddings_manager.use_pinecone and embeddings_manager.pinecone_ready):
            # Fallback to regular semantic search
            return await search_legal_texts(query)
        
        # Import pinecone_store
        from .vector_store import pinecone_store
        
        # Create query embedding
        query_embedding = embeddings_manager.model.encode([query.query])
        
        # Perform hybrid search with filters
        keyword_filters = {}
        
        # You can add more sophisticated keyword extraction here
        query_words = query.query.lower().split()
        if len(query_words) > 0:
            keyword_filters['content_keywords'] = query_words
        
        results = await pinecone_store.hybrid_search(
            query_embedding[0],
            keyword_filters,
            query.language,
            query.max_results
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "type": result.get('type', 'unknown'),
                "title": result.get('title', ''),
                "content": result.get('content', ''),
                "similarity_score": result.get('score', 0),
                "rank": result.get('rank', 0),
                "source": result.get('source', 'unknown'),
                "search_method": "hybrid",
                "keyword_match": result.get('keyword_match', False)
            }
            
            # Add specific fields based on type
            if result.get('type') == 'article':
                formatted_result["article_number"] = result.get('article_number')
                formatted_result["section"] = result.get('section', '')
            elif result.get('type') == 'appendix':
                formatted_result["appendix_number"] = result.get('appendix_number')
                
            formatted_results.append(formatted_result)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        
        return SearchResponse(
            query=query.query,
            results=formatted_results,
            total_found=len(formatted_results),
            processing_time=round(processing_time, 3),
            integrity_check=integrity
        )
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

@app.get("/api/pinecone/stats")
async def get_pinecone_stats():
    """إحصائيات Pinecone"""
    try:
        if not (embeddings_manager.use_pinecone and embeddings_manager.pinecone_ready):
            return {"status": "not_available", "message": "Pinecone not initialized"}
        
        from .vector_store import pinecone_store
        return await pinecone_store.get_index_stats()
        
    except Exception as e:
        logger.error(f"Pinecone stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point for Vercel
app_handler = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)