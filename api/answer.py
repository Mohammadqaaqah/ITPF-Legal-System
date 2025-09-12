#!/usr/bin/env python3
"""
ITPF Legal System - Complete DeepSeek Integration
نظام ITPF القانوني مع تكامل DeepSeek كامل ومتقدم
"""

import json
import os
import re
import requests
from typing import Dict, Any, List, Tuple
from http.server import BaseHTTPRequestHandler

class ITTPFLegalSystem:
    """نظام ITPF القانوني الكامل مع DeepSeek"""
    
    def __init__(self):
        """تهيئة النظام"""
        self.arabic_data = {}
        self.english_data = {}
        self.deepseek_api_key = None
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        
        # تحميل قواعد البيانات
        self._load_databases()
        
        # تهيئة مفاتيح DeepSeek
        self._initialize_deepseek()
    
    def _load_databases(self):
        """تحميل قواعد البيانات العربية والإنجليزية"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # تحميل البيانات العربية
            arabic_file = os.path.join(script_dir, 'arabic_legal_rules_complete_authentic.json')
            with open(arabic_file, 'r', encoding='utf-8') as f:
                self.arabic_data = json.load(f)
            
            # تحميل البيانات الإنجليزية  
            english_file = os.path.join(script_dir, 'english_legal_rules_complete_authentic.json')
            with open(english_file, 'r', encoding='utf-8') as f:
                self.english_data = json.load(f)
                
            print(f"✅ قواعد البيانات محملة - عربي: {len(self.arabic_data['articles'])} مادة + {len(self.arabic_data['appendices'])} ملحق")
            print(f"✅ قواعد البيانات محملة - إنجليزي: {len(self.english_data['articles'])} مادة + {len(self.english_data['appendices'])} ملحق")
            
        except Exception as e:
            print(f"❌ خطأ في تحميل قواعد البيانات: {str(e)}")
    
    def _initialize_deepseek(self):
        """تهيئة مفاتيح DeepSeek API من بيئة Vercel"""
        # قائمة بجميع المفاتيح المحتملة في بيئة Vercel
        potential_keys = [
            'DEEPSEEK_API_KEY',
            'DEEPSEEK_API_KEY_1', 
            'DEEPSEEK_API_KEY_2',
            'DEEPSEEK_API_KEY_3',
            'deepseek_api_key',
            'DEEPSEEK_TOKEN',
            'deepseek_token'
        ]
        
        print("🔍 البحث عن مفاتيح DeepSeek في بيئة Vercel...")
        
        # محاولة قراءة كل مفتاح من البيئة
        for key_name in potential_keys:
            try:
                value = os.environ.get(key_name, '').strip()
                if value and len(value) > 20 and value.startswith('sk-'):
                    self.deepseek_api_key = value
                    print(f"✅ تم العثور على مفتاح DeepSeek صحيح: {key_name}")
                    print(f"🔑 طول المفتاح: {len(value)} - المقطع الأول: {value[:12]}...")
                    return
                elif value:
                    print(f"⚠️ مفتاح غير صحيح في {key_name}: طول={len(value)}, يبدأ بـ sk-={value.startswith('sk-') if value else False}")
            except Exception as e:
                print(f"❌ خطأ في قراءة {key_name}: {str(e)}")
        
        # طباعة جميع متغيرات البيئة للتشخيص (فقط في التطوير)
        all_env_vars = {k: v[:10] + "..." if len(v) > 10 else v for k, v in os.environ.items() if 'deepseek' in k.lower() or 'api' in k.lower()}
        if all_env_vars:
            print(f"🔍 متغيرات البيئة ذات الصلة: {list(all_env_vars.keys())}")
        else:
            print("❌ لم يتم العثور على أي مفاتيح API في بيئة Vercel!")
            
        if not self.deepseek_api_key:
            print("❌ تعذر العثور على مفتاح DeepSeek API صحيح في بيئة Vercel!")
            print("💡 تأكد من إضافة مفتاح DeepSeek في إعدادات Environment Variables في Vercel")
    
    def search_legal_content(self, question: str, language: str) -> List[Dict[str, Any]]:
        """البحث في المحتوى القانوني"""
        data = self.arabic_data if language == 'arabic' else self.english_data
        results = []
        
        # تحويل السؤال إلى كلمات مفتاحية
        keywords = self._extract_keywords(question, language)
        
        # البحث في المواد القانونية
        for article in data['articles']:
            score = self._calculate_relevance(question, keywords, article['content'], language)
            if score > 0:
                results.append({
                    'type': 'article',
                    'article_number': article['article_number'],
                    'title': article.get('title', f'المادة {article["article_number"]}'),
                    'content': article['content'][:500],  # أول 500 حرف
                    'score': score
                })
        
        # البحث في الملاحق
        for appendix in data['appendices']:
            score = self._calculate_relevance(question, keywords, str(appendix['content']), language)
            if score > 0:
                results.append({
                    'type': 'appendix', 
                    'appendix_number': appendix['appendix_number'],
                    'title': appendix.get('title', f'ملحق {appendix["appendix_number"]}'),
                    'content': str(appendix['content'])[:500],
                    'score': score
                })
        
        # ترتيب النتائج حسب الصلة
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:10]  # أفضل 10 نتائج
    
    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """استخراج الكلمات المفتاحية"""
        if language == 'arabic':
            # كلمات مفتاحية عربية
            legal_terms = ['فريق', 'متسابق', 'نقاط', 'جزاء', 'مسابقة', 'خيل', 'رمح', 'سيف', 'وتد', 'حكام', 'قانون', 'مادة']
        else:
            legal_terms = ['team', 'rider', 'points', 'penalty', 'competition', 'horse', 'lance', 'sword', 'peg', 'judge', 'rule', 'article']
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2]
        keywords.extend([term for term in legal_terms if term in text.lower()])
        
        return list(set(keywords))
    
    def _calculate_relevance(self, question: str, keywords: List[str], content: str, language: str) -> float:
        """حساب درجة الصلة"""
        score = 0.0
        content_lower = content.lower()
        question_lower = question.lower()
        
        # تطابق مباشر مع السؤال
        if any(word in content_lower for word in question_lower.split() if len(word) > 2):
            score += 10.0
            
        # تطابق الكلمات المفتاحية
        for keyword in keywords:
            if keyword in content_lower:
                score += 5.0
        
        # تطابق الأرقام (مهم للمواد والجزاءات)
        numbers_in_question = re.findall(r'\d+', question)
        numbers_in_content = re.findall(r'\d+', content)
        common_numbers = set(numbers_in_question) & set(numbers_in_content)
        score += len(common_numbers) * 15.0
        
        return score
    
    def generate_deepseek_response(self, question: str, legal_context: List[Dict[str, Any]], language: str) -> str:
        """توليد إجابة ذكية باستخدام DeepSeek"""
        
        # إعادة محاولة تهيئة المفتاح إذا لم يكن متاحاً
        if not self.deepseek_api_key:
            self._initialize_deepseek()
        
        if not self.deepseek_api_key:
            print("🔄 إعادة محاولة قراءة مفاتيح DeepSeek من البيئة...")
            return self._generate_fallback_response(question, legal_context, language)
        
        try:
            # إعداد السياق القانوني لـ DeepSeek
            context_text = ""
            for item in legal_context[:5]:  # أفضل 5 نتائج
                if item['type'] == 'article':
                    context_text += f"المادة {item['article_number']}: {item['title']}\n{item['content']}\n\n"
                else:
                    context_text += f"ملحق {item['appendix_number']}: {item['title']}\n{item['content']}\n\n"
            
            # إعداد البرومبت للغة المحددة
            if language == 'arabic':
                system_prompt = """أنت خبير قانوني متخصص في قوانين الاتحاد الدولي لالتقاط الأوتاد (ITPF). 

## مهمتك:
1. تحليل السؤال القانوني بعمق ودقة
2. تقديم إجابة محددة وعملية بناءً على القوانين المتاحة
3. تجنب الإجابات العامة والتركيز على السيناريو المحدد
4. الإجابة باللغة العربية فقط مع التنظيم المهني

## التعليمات المحددة:
- استخدم فقط المراجع القانونية المتاحة
- قدم تحليل قانوني عملي ومحدد
- اذكر أرقام المواد والملاحق ذات الصلة بوضوح
- تجنب خلط اللغات نهائياً
- انتبه لنظام النقاط والخصومات (6 نقاط للحمل، 4 للنزع، 2 للطعن)
- انتبه لجدول خصومات الوقت (0.5 نقطة لكل ثانية تجاوز)

## تنسيق الإجابة المطلوب:
استخدم هذا التنسيق الدقيق:

### 🔍 **التحليل القانوني المنظم:**

#### **1️⃣ [العنوان الأول]:**
**المادة [رقم]: [اسم المادة]**
- ✅ أو ❌ [التحليل]
- 📊 [التفاصيل إن وجدت]

#### **2️⃣ [العنوان الثاني]:**
**المادة [رقم]: [اسم المادة]**  
- ⚖️ [التطبيق القانوني]

### 🎯 **القرار النهائي:**
- **الحكم:** [القرار المحدد]
- **الأساس القانوني:** المواد [أرقام المواد]"""
                
                user_prompt = f"""السؤال: {question}

المراجع القانونية المتاحة:
{context_text}

المطلوب: تحليل قانوني محدد ومفصل للسؤال، مع ذكر المواد القانونية ذات الصلة."""
                
            else:
                system_prompt = """You are a legal expert specialized in the International Tent Pegging Federation (ITPF) rules.

## Your task:
1. Analyze the legal question thoroughly and accurately
2. Provide specific and practical answers based on available laws
3. Avoid general answers and focus on the specific scenario
4. Answer in English only with professional organization

## Specific Instructions:
- Use only the available legal references
- Provide practical and specific legal analysis
- Mention relevant article and appendix numbers clearly
- Avoid mixing languages completely
- Pay attention to scoring system and penalties (6 points for carry, 4 for lift, 2 for hit)
- Pay attention to time penalty table (0.5 points per second over limit)

## Required Answer Format:
Use this exact formatting:

### 🔍 **Organized Legal Analysis:**

#### **1️⃣ [First Section Title]:**
**Article [number]: [Article Name]**
- ✅ or ❌ [Analysis]
- 📊 [Details if applicable]

#### **2️⃣ [Second Section Title]:**
**Article [number]: [Article Name]**  
- ⚖️ [Legal Application]

### 🎯 **Final Decision:**
- **Ruling:** [Specific Decision]
- **Legal Basis:** Articles [article numbers]"""
                
                user_prompt = f"""Question: {question}

Available Legal References:
{context_text}

Required: Specific and detailed legal analysis of the question, citing relevant legal articles."""
            
            # إرسال الطلب إلى DeepSeek
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 800
            }
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"🤖 استدعاء DeepSeek API...")
            
            response = requests.post(self.deepseek_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content']
                    print(f"✅ DeepSeek نجح: {len(ai_response)} حرف")
                    return ai_response
                else:
                    print(f"❌ استجابة DeepSeek غير صحيحة: {result}")
                    return self._generate_fallback_response(question, legal_context, language)
            else:
                print(f"❌ خطأ DeepSeek API {response.status_code}: {response.text}")
                return self._generate_fallback_response(question, legal_context, language)
                
        except Exception as e:
            print(f"❌ خطأ DeepSeek: {str(e)}")
            return self._generate_fallback_response(question, legal_context, language)
    
    def _generate_fallback_response(self, question: str, legal_context: List[Dict[str, Any]], language: str) -> str:
        """توليد إجابة احتياطية عند فشل DeepSeek"""
        if language == 'arabic':
            response = "## الخلاصة القانونية\n\n"
            response += "بناءً على تحليل القوانين المتاحة:\n\n"
            
            for i, item in enumerate(legal_context[:3], 1):
                if item['type'] == 'article':
                    response += f"**{i}. المادة {item['article_number']}**: {item['title']}\n"
                    response += f"   {item['content'][:200]}...\n\n"
                else:
                    response += f"**{i}. ملحق {item['appendix_number']}**: {item['title']}\n"
                    response += f"   {item['content'][:200]}...\n\n"
            
            return response
        else:
            response = "## Legal Summary\n\n"
            response += "Based on analysis of available laws:\n\n"
            
            for i, item in enumerate(legal_context[:3], 1):
                if item['type'] == 'article':
                    response += f"**{i}. Article {item['article_number']}**: {item['title']}\n"
                    response += f"   {item['content'][:200]}...\n\n"
                else:
                    response += f"**{i}. Appendix {item['appendix_number']}**: {item['title']}\n"
                    response += f"   {item['content'][:200]}...\n\n"
            
            return response

    def process_question(self, question: str, language: str = 'arabic') -> Dict[str, Any]:
        """معالجة السؤال وإرجاع الإجابة الكاملة"""
        
        # البحث في المحتوى القانوني
        legal_context = self.search_legal_content(question, language)
        
        # توليد الإجابة الذكية
        ai_response = self.generate_deepseek_response(question, legal_context, language)
        
        # إعداد المراجع القانونية
        references = []
        for item in legal_context[:6]:
            ref = {
                'type': item['type'],
                'number': item.get('article_number') or item.get('appendix_number'),
                'title': item['title'], 
                'content': item['content'][:300],
                'relevance_score': item['score']
            }
            references.append(ref)
        
        return {
            'success': True,
            'legal_analysis': ai_response,
            'legal_references': references,
            'metadata': {
                'question': question,
                'language': language,
                'references_found': len(legal_context),
                'deepseek_used': bool(self.deepseek_api_key),
                'articles_count': len(self.arabic_data['articles']),
                'appendices_count': len(self.arabic_data['appendices'])
            }
        }

# إنشاء المثيل العالمي
itpf_system = ITTPFLegalSystem()

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    """معالج Vercel الرئيسي للنظام المتطور"""
    
    def do_OPTIONS(self):
        """معالجة CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """معالجة طلبات POST"""
        try:
            # قراءة البيانات
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            question = data.get('question', '')
            language = data.get('language', 'arabic')
            
            if not question:
                self.send_error_response({'error': 'السؤال مطلوب'}, 400)
                return
            
            # معالجة السؤال بالنظام المتطور
            result = itpf_system.process_question(question, language)
            
            # إرسال الاستجابة
            self.send_success_response(result)
            
        except Exception as e:
            self.send_error_response({'error': str(e)}, 500)
    
    def send_success_response(self, data):
        """إرسال استجابة ناجحة"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, error_data, status_code):
        """إرسال استجابة خطأ"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(error_data, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))

# للاختبار المحلي
if __name__ == "__main__":
    # اختبار النظام محلياً
    test_question = "فريق حصل على 15 نقطة جزاء، ما الحكم القانوني؟"
    result = itpf_system.process_question(test_question, 'arabic')
    print(json.dumps(result, ensure_ascii=False, indent=2))