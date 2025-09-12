"""
ITPF Legal Search API - Search Endpoint for Vercel
Individual function for search endpoint
"""

import json
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime


def load_data():
    """Load legal data from split JSON files"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load Arabic data from split files
    arabic_data = {"metadata": {}, "articles": []}
    for i in range(1, 4):  # Load parts 1, 2, 3
        arabic_file = os.path.join(current_dir, f"arabic_data_part{i}.json")
        if os.path.exists(arabic_file):
            with open(arabic_file, 'r', encoding='utf-8') as f:
                part_data = json.load(f)
                if i == 1:  # Get metadata from first part
                    arabic_data["metadata"] = part_data.get("metadata", {})
                arabic_data["articles"].extend(part_data.get("articles", []))
    
    # Load English data from split files
    english_data = {"metadata": {}, "chapters": []}
    for i in range(1, 4):  # Load parts 1, 2, 3
        english_file = os.path.join(current_dir, f"english_data_part{i}.json")
        if os.path.exists(english_file):
            with open(english_file, 'r', encoding='utf-8') as f:
                part_data = json.load(f)
                if i == 1:  # Get metadata from first part
                    english_data["metadata"] = part_data.get("metadata", {})
                english_data["chapters"].extend(part_data.get("chapters", []))
    
    # If no split files found, try original files as fallback
    if not arabic_data["articles"]:
        arabic_file = os.path.join(current_dir, "../arabic_legal_rules_complete_authentic.json")
        if os.path.exists(arabic_file):
            with open(arabic_file, 'r', encoding='utf-8') as f:
                arabic_data = json.load(f)
    
    if not english_data["chapters"]:
        english_file = os.path.join(current_dir, "../english_legal_rules_complete_authentic.json")
        if os.path.exists(english_file):
            with open(english_file, 'r', encoding='utf-8') as f:
                english_data = json.load(f)
                
    return arabic_data, english_data


def simple_search(query: str, language: str = "both", max_results: int = 10, arabic_data=None, english_data=None) -> List[Dict[str, Any]]:
    """Simple text search without embeddings"""
    results = []
    query_lower = query.lower()
    
    # Search Arabic data
    if language in ["ar", "arabic", "both"] and arabic_data:
        arabic_articles = arabic_data.get('articles', [])
        for item in arabic_articles:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            
            if query_lower in title or query_lower in content:
                # Calculate simple relevance score
                title_matches = title.count(query_lower)
                content_matches = content.count(query_lower)
                score = min(95, (title_matches * 10 + content_matches * 5) * 10)
                
                results.append({
                    "title": item.get('title', ''),
                    "content": item.get('content', ''),
                    "score": score,
                    "source": {
                        "article": f"المادة {item.get('article_number', '')}",
                        "section": item.get('section', 'قواعد ITPF'),
                        "document": "قواعد الاتحاد الدولي لالتقاط الأوتاد"
                    },
                    "highlights": [query],
                    "language": "arabic"
                })
                if len(results) >= max_results:
                    break
    
    # Search English data
    if language in ["en", "english", "both"] and english_data and len(results) < max_results:
        # Handle both direct articles and chapters/articles structure
        english_articles = english_data.get('articles', [])
        
        # If no direct articles, extract from chapters
        if not english_articles and 'chapters' in english_data:
            for chapter in english_data['chapters']:
                english_articles.extend(chapter.get('articles', []))
        
        for item in english_articles:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            
            if query_lower in title or query_lower in content:
                # Calculate simple relevance score
                title_matches = title.count(query_lower)
                content_matches = content.count(query_lower)
                score = min(95, (title_matches * 10 + content_matches * 5) * 10)
                
                results.append({
                    "title": item.get('title', ''),
                    "content": item.get('content', ''),
                    "score": score,
                    "source": {
                        "article": f"Article {item.get('article_number', '')}",
                        "section": item.get('section', 'ITPF Rules'),
                        "document": "International Tent Pegging Federation Rules"
                    },
                    "highlights": [query],
                    "language": "english"
                })
                if len(results) >= max_results:
                    break
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:max_results]


from http.server import BaseHTTPRequestHandler
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Set CORS headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
            except:
                data = {}
            
            query = data.get("query", "").strip()
            language = data.get("language", "both")
            max_results = min(data.get("max_results", 10), 50)
            
            if not query:
                response = {
                    "success": False,
                    "message": "Query is required"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            if len(query) < 2:
                response = {
                    "success": False,
                    "message": "Query must be at least 2 characters long"
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Load data and perform search
            arabic_data, english_data = load_data()
            results = simple_search(query, language, max_results, arabic_data, english_data)
            
            # Format response
            response = {
                "success": True,
                "hasResults": len(results) > 0,
                "message": f"Found {len(results)} results" if len(results) > 0 else "No results found",
                "results": results,
                "metadata": {
                    "query": query,
                    "language": language,
                    "search_time": "< 1000ms",
                    "total_results": len(results)
                }
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "success": False,
                "message": f"Search error: {str(e)}"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_GET(self):
        """Handle GET requests - show API info"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "ITPF Legal Search API",
            "version": "1.0.0",
            "status": "active",
            "endpoint": "/api/search",
            "method": "POST",
            "usage": {
                "query": "search term",
                "language": "both|arabic|english"
            }
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))