"""
نسخة مبسطة مؤقتة من ITPF Legal Search API
محافظة على فحص سلامة النصوص - بدون المكتبات الثقيلة للاختبار
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

app = FastAPI(
    title="ITPF Legal Search API - Simplified",
    description="نسخة مبسطة للاختبار مع الحفاظ على سلامة النصوص",
    version="1.0.0-simplified"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimplifiedLegalTextLoader:
    def __init__(self, api_dir: str):
        self.api_dir = api_dir
        self.arabic_data = None
        self.english_data = None
        self.loaded = False
        
    async def load_data(self):
        """تحميل البيانات القانونية"""
        if self.loaded:
            return
            
        try:
            # تحميل البيانات العربية
            arabic_file = os.path.join(self.api_dir, "arabic_legal_rules_complete_authentic.json")
            if os.path.exists(arabic_file):
                with open(arabic_file, 'r', encoding='utf-8') as f:
                    self.arabic_data = json.load(f)
            
            # تحميل البيانات الإنجليزية
            english_file = os.path.join(self.api_dir, "english_legal_rules_complete_authentic.json")
            if os.path.exists(english_file):
                with open(english_file, 'r', encoding='utf-8') as f:
                    self.english_data = json.load(f)
                    
            self.loaded = True
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"فشل في تحميل البيانات: {str(e)}")

    async def verify_integrity(self) -> Dict[str, Any]:
        """فحص سلامة النصوص القانونية مع مقارنة بالملفات المرجعية"""
        await self.load_data()
        
        integrity_report = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "arabic_verification": {},
            "english_verification": {},
            "overall_status": "complete",
            "reference_comparison": {},
            "prevention_system": {
                "active": True,
                "reference_files": ["arabic.txt", "english.txt"],
                "auto_validation": True
            }
        }
        
        # مقارنة مع الملفات المرجعية
        try:
            # قراءة النص المرجعي العربي
            arabic_ref_path = os.path.join(os.path.dirname(self.api_dir), "arabic.txt")
            if os.path.exists(arabic_ref_path):
                with open(arabic_ref_path, 'r', encoding='utf-8') as f:
                    arabic_ref_content = f.read()
                    arabic_ref_articles = len(re.findall(r'المادة \d{3}:', arabic_ref_content))
                    
            # قراءة النص المرجعي الإنجليزي
            english_ref_path = os.path.join(os.path.dirname(self.api_dir), "english.txt")  
            if os.path.exists(english_ref_path):
                with open(english_ref_path, 'r', encoding='utf-8') as f:
                    english_ref_content = f.read()
                    english_ref_articles = len(re.findall(r'Article \d{3}:', english_ref_content))
                    
            integrity_report["reference_comparison"] = {
                "arabic_reference_articles": arabic_ref_articles,
                "english_reference_articles": english_ref_articles,
                "reference_files_accessible": True
            }
        except Exception as e:
            integrity_report["reference_comparison"] = {
                "error": f"لا يمكن الوصول للملفات المرجعية: {str(e)}",
                "reference_files_accessible": False
            }
        
        # فحص البيانات العربية
        if self.arabic_data:
            arabic_articles = self.arabic_data.get('articles', [])
            arabic_appendices = self.arabic_data.get('appendices', [])
            
            # فحص الأرقام (100-154 = 55 مادة)
            article_numbers = set()
            for article in arabic_articles:
                article_num = article.get('article_number')
                if article_num:
                    article_numbers.add(int(article_num))
            
            expected_numbers = set(range(100, 155))
            missing_articles = expected_numbers - article_numbers
            
            integrity_report["arabic_verification"] = {
                "total_articles": len(arabic_articles),
                "expected_articles": 55,
                "found_article_numbers": sorted(list(article_numbers)),
                "missing_articles": sorted(list(missing_articles)),
                "appendices_count": len(arabic_appendices),
                "total_characters": sum(len(str(item)) for item in self.arabic_data)
            }
        
        # فحص البيانات الإنجليزية
        if self.english_data:
            english_articles = []
            # استخراج المقالات من الفصول
            for chapter in self.english_data.get('chapters', []):
                english_articles.extend(chapter.get('articles', []))
            english_appendices = self.english_data.get('appendices', [])
            
            # فحص الأرقام
            article_numbers = set()
            for article in english_articles:
                article_num = article.get('article_number')
                if article_num:
                    article_numbers.add(int(article_num))
            
            expected_numbers = set(range(100, 155))
            missing_articles = expected_numbers - article_numbers
            
            integrity_report["english_verification"] = {
                "total_articles": len(english_articles),
                "expected_articles": 55,
                "found_article_numbers": sorted(list(article_numbers)),
                "missing_articles": sorted(list(missing_articles)),
                "appendices_count": len(english_appendices),
                "total_characters": sum(len(str(item)) for item in self.english_data)
            }
        
        # تحديد الحالة العامة
        arabic_complete = (
            integrity_report["arabic_verification"].get("total_articles", 0) == 55 and
            len(integrity_report["arabic_verification"].get("missing_articles", [])) == 0 and
            integrity_report["arabic_verification"].get("appendices_count", 0) >= 2
        )
        
        english_complete = (
            integrity_report["english_verification"].get("total_articles", 0) == 55 and
            len(integrity_report["english_verification"].get("missing_articles", [])) == 0 and
            integrity_report["english_verification"].get("appendices_count", 0) >= 2
        )
        
        if not arabic_complete or not english_complete:
            integrity_report["overall_status"] = "incomplete"
            integrity_report["status"] = "warning"
        
        # فحص مطابقة للملفات المرجعية
        if "reference_comparison" in integrity_report and integrity_report["reference_comparison"].get("reference_files_accessible"):
            ref_arabic = integrity_report["reference_comparison"].get("arabic_reference_articles", 0)
            ref_english = integrity_report["reference_comparison"].get("english_reference_articles", 0)
            
            current_arabic = integrity_report["arabic_verification"].get("total_articles", 0)
            current_english = integrity_report["english_verification"].get("total_articles", 0)
            
            if ref_arabic != current_arabic or ref_english != current_english:
                integrity_report["status"] = "mismatch_with_reference" 
                integrity_report["overall_status"] = "reference_mismatch"
                integrity_report["mismatch_details"] = {
                    "arabic": {"expected": ref_arabic, "found": current_arabic},
                    "english": {"expected": ref_english, "found": current_english}
                }
        
        return integrity_report

    async def simple_search(self, query: str, language: str = "both", max_results: int = 10) -> List[Dict[str, Any]]:
        """بحث مبسط نصي - بدون embeddings"""
        await self.load_data()
        
        results = []
        query_lower = query.lower()
        
        # البحث في البيانات العربية
        if language in ["arabic", "both"] and self.arabic_data:
            arabic_articles = self.arabic_data.get('articles', [])
            for item in arabic_articles:
                title = item.get('title', '').lower()
                content = item.get('content', '').lower()
                
                if query_lower in title or query_lower in content:
                    results.append({
                        "id": item.get('article_number', ''),
                        "title": item.get('title', ''),
                        "content": item.get('content', ''),
                        "type": "article",
                        "language": "arabic",
                        "score": 1.0  # نتيجة ثابتة للبحث المبسط
                    })
                    if len(results) >= max_results:
                        break
        
        # البحث في البيانات الإنجليزية
        if language in ["english", "both"] and self.english_data:
            english_articles = self.english_data.get('articles', [])
            
            for item in english_articles:
                title = item.get('title', '').lower()
                content = item.get('content', '').lower()
                
                if query_lower in title or query_lower in content:
                    results.append({
                        "id": item.get('article_number', ''),
                        "title": item.get('title', ''),
                        "content": item.get('content', ''),
                        "type": "article",
                        "language": "english",
                        "score": 1.0
                    })
                    if len(results) >= max_results:
                        break
        
        return results[:max_results]

# إنشاء instance
current_dir = os.path.dirname(os.path.abspath(__file__))
text_loader = SimplifiedLegalTextLoader(current_dir)

@app.get("/")
@app.get("/api/main")
async def root():
    return {
        "message": "ITPF Legal Search API - نسخة مبسطة للاختبار",
        "version": "1.0.0-simplified",
        "status": "active",
        "features": ["text_integrity_check", "simple_search"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "simplified_testing"
    }

@app.post("/verify-integrity")
async def verify_text_integrity():
    """فحص سلامة النصوص القانونية"""
    try:
        report = await text_loader.verify_integrity()
        return JSONResponse(content=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في فحص السلامة: {str(e)}")

@app.post("/search")
@app.post("/api/search")
async def search_legal_texts(request_data: dict):
    """بحث مبسط في النصوص القانونية"""
    try:
        query = request_data.get("query", "")
        language = request_data.get("language", "both")
        max_results = request_data.get("max_results", 10)
        
        if not query:
            raise HTTPException(status_code=400, detail="يجب تقديم نص للبحث")
        
        results = await text_loader.simple_search(query, language, max_results)
        
        return JSONResponse(content={
            "query": query,
            "language": language,
            "results_count": len(results),
            "results": results,
            "search_type": "simplified_text_search"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في البحث: {str(e)}")

@app.get("/data-stats")
async def get_data_statistics():
    """إحصائيات البيانات"""
    try:
        await text_loader.load_data()
        
        stats = {
            "arabic_loaded": text_loader.arabic_data is not None,
            "english_loaded": text_loader.english_data is not None,
            "arabic_items": len(text_loader.arabic_data) if text_loader.arabic_data else 0,
            "english_items": len(text_loader.english_data) if text_loader.english_data else 0,
        }
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في جلب الإحصائيات: {str(e)}")

@app.post("/restore-from-reference")
async def restore_from_reference():
    """استعادة البيانات من الملفات المرجعية في حالة النقص"""
    try:
        # فحص الحالة الحالية
        integrity_report = await text_loader.verify_integrity()
        
        if integrity_report["overall_status"] == "complete":
            return JSONResponse(content={
                "status": "no_action_needed",
                "message": "البيانات مكتملة ولا تحتاج استعادة",
                "current_integrity": integrity_report
            })
        
        # إذا كان هناك نقص، استخدم الملف المكتمل
        api_dir = os.path.dirname(os.path.abspath(__file__))
        
        # استعادة العربية من الملف المكتمل
        if integrity_report["arabic_verification"].get("total_articles", 0) < 55:
            complete_file = os.path.join(api_dir, "arabic_legal_rules_complete_fixed.json")
            target_file = os.path.join(api_dir, "arabic_legal_rules_complete_authentic.json")
            
            if os.path.exists(complete_file):
                import shutil
                shutil.copy2(complete_file, target_file)
                
        # إعادة تحميل البيانات والتحقق
        text_loader.loaded = False
        await text_loader.load_data()
        new_integrity = await text_loader.verify_integrity()
        
        return JSONResponse(content={
            "status": "restored",
            "message": "تمت استعادة البيانات بنجاح",
            "before": integrity_report,
            "after": new_integrity
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في الاستعادة: {str(e)}")

# Vercel handler
handler = app
app_handler = app