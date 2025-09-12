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
        """تهيئة مفاتيح DeepSeek API"""
        potential_keys = ['DEEPSEEK_API_KEY', 'DEEPSEEK_API_KEY_1', 'DEEPSEEK_API_KEY_2', 'DEEPSEEK_API_KEY_3']
        
        for key_name in potential_keys:
            value = os.environ.get(key_name)
            if value and len(value) > 20:
                self.deepseek_api_key = value
                print(f"🔑 DeepSeek API Key جاهز: {key_name}")
                break
        
        if not self.deepseek_api_key:
            print("❌ لا توجد مفاتيح DeepSeek API!")
    
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
        
        if not self.deepseek_api_key:
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
                
مهمتك:
1. تحليل السؤال القانوني بعمق
2. تقديم إجابة محددة وعملية بناءً على القوانين المتاحة
3. تجنب الإجابات العامة والتركيز على السيناريو المحدد
4. الإجابة باللغة العربية فقط

التعليمات:
- استخدم فقط المراجع القانونية المتاحة
- قدم تحليل قانوني عملي ومحدد
- اذكر أرقام المواد والملاحق ذات الصلة
- تجنب خلط اللغات"""
                
                user_prompt = f"""السؤال: {question}

المراجع القانونية المتاحة:
{context_text}

المطلوب: تحليل قانوني محدد ومفصل للسؤال، مع ذكر المواد القانونية ذات الصلة."""
                
            else:
                system_prompt = """You are a legal expert specialized in the International Tent Pegging Federation (ITPF) rules.

Your task:
1. Analyze the legal question thoroughly  
2. Provide specific and practical answers based on available laws
3. Avoid general answers and focus on the specific scenario
4. Answer in English only

Instructions:
- Use only the available legal references
- Provide practical and specific legal analysis
- Mention relevant article and appendix numbers
- Avoid mixing languages"""
                
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

def handler(event, context):
    """معالج Vercel الرئيسي"""
    try:
        # استخراج البيانات من الطلب
        if hasattr(event, 'get_json'):
            data = event.get_json()
        else:
            data = json.loads(event.get('body', '{}'))
        
        question = data.get('question', '')
        language = data.get('language', 'arabic')
        
        if not question:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json; charset=utf-8'},
                'body': json.dumps({'error': 'السؤال مطلوب'}, ensure_ascii=False)
            }
        
        # معالجة السؤال
        result = itpf_system.process_question(question, language)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps(result, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json; charset=utf-8'},
            'body': json.dumps({'error': str(e)}, ensure_ascii=False)
        }

# للاختبار المحلي
if __name__ == "__main__":
    # اختبار النظام محلياً
    test_question = "فريق حصل على 15 نقطة جزاء، ما الحكم القانوني؟"
    result = itpf_system.process_question(test_question, 'arabic')
    print(json.dumps(result, ensure_ascii=False, indent=2))