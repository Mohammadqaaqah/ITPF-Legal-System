"""
Debug endpoint to check file accessibility on Vercel
"""

import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Debug endpoint to check file structure and data files"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check what files exist
        files_in_api = []
        if os.path.exists(current_dir):
            files_in_api = os.listdir(current_dir)
        
        # Check for data files specifically
        arabic_file = os.path.join(current_dir, "arabic_legal_rules_complete_authentic.json")
        english_file = os.path.join(current_dir, "english_legal_rules_complete_authentic.json")
        
        arabic_exists = os.path.exists(arabic_file)
        english_exists = os.path.exists(english_file)
        
        arabic_size = 0
        english_size = 0
        
        if arabic_exists:
            arabic_size = os.path.getsize(arabic_file)
        if english_exists:
            english_size = os.path.getsize(english_file)
        
        # Try to load a small sample from each file
        arabic_sample = None
        english_sample = None
        
        if arabic_exists:
            try:
                with open(arabic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'articles' in data and len(data['articles']) > 0:
                        arabic_sample = {
                            "total_articles": len(data['articles']),
                            "first_article_title": data['articles'][0].get('title', '')[:100],
                            "appendices": len(data.get('appendices', []))
                        }
            except Exception as e:
                arabic_sample = f"Error loading: {str(e)}"
        
        if english_exists:
            try:
                with open(english_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_articles = 0
                    first_title = ""
                    for chapter in data.get('chapters', []):
                        articles = chapter.get('articles', [])
                        total_articles += len(articles)
                        if not first_title and len(articles) > 0:
                            first_title = articles[0].get('title', '')[:100]
                    
                    english_sample = {
                        "total_chapters": len(data.get('chapters', [])),
                        "total_articles": total_articles,
                        "first_article_title": first_title,
                        "appendices": len(data.get('appendices', []))
                    }
            except Exception as e:
                english_sample = f"Error loading: {str(e)}"
        
        response = {
            "current_directory": current_dir,
            "files_in_api_directory": files_in_api,
            "arabic_file_exists": arabic_exists,
            "english_file_exists": english_exists,
            "arabic_file_size": arabic_size,
            "english_file_size": english_size,
            "arabic_data_sample": arabic_sample,
            "english_data_sample": english_sample,
            "debug_timestamp": "2025-01-08 12:00:00"
        }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))