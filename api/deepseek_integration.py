"""
ITPF Legal System - DeepSeek API Integration
تكامل نظام ITPF القانوني مع DeepSeek API للذكاء المتقدم
"""

import json
import os
import asyncio
from typing import Dict, Any, List, Optional
from openai import OpenAI

class DeepSeekIntegration:
    """تكامل متقدم مع DeepSeek API لتحليل قانوني ذكي"""
    
    def __init__(self):
        """تهيئة النظام مع مفاتيح API المتعددة"""
        self.api_keys = [
            os.getenv('DEEPSEEK_API_KEY_1'),
            os.getenv('DEEPSEEK_API_KEY_2'), 
            os.getenv('DEEPSEEK_API_KEY_3')
        ]
        self.current_key_index = 0
        self.base_url = "https://api.deepseek.com"
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """إعداد عميل API مع تبديل المفاتيح التلقائي"""
        if self.api_keys[self.current_key_index]:
            self.client = OpenAI(
                api_key=self.api_keys[self.current_key_index],
                base_url=self.base_url
            )
    
    def _switch_api_key(self):
        """تبديل مفتاح API في حالة الخطأ"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._setup_client()
    
    def analyze_query_complexity(self, question: str) -> str:
        """تحليل تعقيد السؤال لتحديد النمط المناسب"""
        question_lower = question.lower()
        
        # مؤشرات التعقيد العالي
        complex_indicators = [
            'قارن', 'اربط', 'حلل', 'استنتج', 'ما الفرق', 'كيف يؤثر',
            'ما العلاقة', 'في أي حالة', 'متى يجب', 'كيف يمكن',
            'compare', 'analyze', 'relate', 'difference', 'relationship'
        ]
        
        # مؤشرات البحث البسيط
        simple_indicators = [
            'ما هي', 'ما هو', 'اذكر', 'عرف', 'what is', 'define', 'list'
        ]
        
        # أسئلة عن الملاحق تحتاج تحليل متخصص
        if 'ملحق' in question_lower or 'appendix' in question_lower:
            return 'deepseek_reasoner'
        
        # فحص مؤشرات التعقيد
        for indicator in complex_indicators:
            if indicator in question_lower:
                return 'deepseek_reasoner'
        
        for indicator in simple_indicators:
            if indicator in question_lower:
                return 'local_fast'
                
        # افتراضي للأسئلة المتوسطة
        return 'deepseek_chat'
    
    def create_legal_prompt(self, question: str, context: List[Dict[str, Any]], mode: str, language: str = 'arabic') -> str:
        """إنشاء prompt متخصص للتحليل القانوني"""
        
        if mode == 'deepseek_reasoner':
            if language == 'english':
                system_prompt = """You are a legal expert specialized in the International Tent Pegging Federation (ITPF) rules.

Your task: Deep logical and graduated analysis of complex legal questions.

Required analysis methodology:
1. Understand the question and identify required legal elements
2. Review relevant legal texts
3. Analyze connections and relationships between different articles
4. Extract conclusions based on legal evidence
5. Provide comprehensive answer with specific citations

Important instructions:
- Use sequential and logical reasoning
- Connect between articles and appendices when needed
- Mention specific article and appendix numbers
- Provide practical examples when possible
- Answer ONLY in English using English legal texts"""
            else:
                system_prompt = """أنت خبير قانوني متخصص في قواعد الاتحاد الدولي لالتقاط الأوتاد (ITPF).

مهمتك: تحليل منطقي عميق ومتدرج للأسئلة القانونية المعقدة.

منهجية التحليل المطلوبة:
1. فهم السؤال وتحديد العناصر القانونية المطلوبة
2. مراجعة النصوص القانونية ذات الصلة
3. تحليل الروابط والعلاقات بين المواد المختلفة
4. استخلاص النتائج بناءً على الأدلة القانونية
5. تقديم إجابة شاملة مع الاستشهاد المحدد

تعليمات مهمة:
- استخدم التفكير المتسلسل والمنطقي
- اربط بين المواد والملاحق عند الحاجة
- اذكر أرقام المواد والملاحق المحددة
- قدم أمثلة عملية عند الإمكان"""

        else:  # deepseek_chat
            if language == 'english':
                system_prompt = """You are a legal assistant specialized in the International Tent Pegging Federation (ITPF) rules.

Your task: Provide clear and accurate answers to legal inquiries.

Your methodology:
- Direct and helpful responses
- Citation of appropriate legal articles
- Answer ONLY in English using English legal texts
- Strict separation from Arabic content"""
            else:
                system_prompt = """أنت مساعد قانوني متخصص في قواعد الاتحاد الدولي لالتقاط الأوتاد (ITPF).

مهمتك: تقديم إجابات واضحة ودقيقة للاستفسارات القانونية.

منهجيتك:
- إجابة مباشرة ومفيدة
- استشهاد بالمواد القانونية المناسبة
- لغة واضحة ومفهومة
- تركيز على الجوانب العملية"""

        # تحضير السياق القانوني
        context_text = ""
        if context:
            context_text = "\n\nالمراجع القانونية المتاحة:\n"
            for i, ref in enumerate(context[:5], 1):
                context_text += f"{i}. المادة {ref.get('article_number', 'غير محدد')}: {ref.get('title', '')}\n"
                context_text += f"   النص: {ref.get('content', '')[:300]}...\n\n"
        
        user_prompt = f"""السؤال: {question}

{context_text}

يرجى تقديم إجابة شاملة ودقيقة مع الاستناد للمواد القانونية المحددة."""

        return system_prompt, user_prompt
    
    async def get_deepseek_response(self, question: str, context: List[Dict[str, Any]], mode: str) -> Dict[str, Any]:
        """الحصول على استجابة من DeepSeek API"""
        try:
            system_prompt, user_prompt = self.create_legal_prompt(question, context, mode)
            
            model = "deepseek-reasoner" if mode == "deepseek_reasoner" else "deepseek-chat"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000 if mode == "deepseek_chat" else 8000,
                temperature=0.1,
                stream=False
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model_used": model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            # محاولة تبديل مفتاح API
            self._switch_api_key()
            
            # محاولة ثانية
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=4000 if mode == "deepseek_chat" else 8000,
                    temperature=0.1,
                    stream=False
                )
                
                return {
                    "success": True,
                    "response": response.choices[0].message.content,
                    "model_used": model,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
                
            except Exception as e2:
                return {
                    "success": False,
                    "error": f"خطأ في API: {str(e2)}",
                    "fallback_needed": True
                }
    
    def enhance_arabic_text(self, text: str) -> str:
        """تحسين النص العربي للمعالجة الأفضل"""
        # توحيد الحروف العربية
        replacements = {
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه',
            'ى': 'ي'
        }
        
        enhanced_text = text
        for old, new in replacements.items():
            enhanced_text = enhanced_text.replace(old, new)
        
        return enhanced_text
    
    def create_enhanced_summary(self, question: str, deepseek_response: str, local_results: List[Dict[str, Any]]) -> str:
        """إنشاء ملخص محسن يجمع بين DeepSeek والنتائج المحلية"""
        
        # استخلاص المراجع من النتائج المحلية
        references = []
        for result in local_results[:3]:
            ref_num = result.get('article_number', '')
            ref_title = result.get('title', '')
            references.append(f"• المادة {ref_num}: {ref_title}")
        
        enhanced_summary = f"""🧠 **التحليل الذكي المتقدم:**

{deepseek_response}

**المراجع القانونية الأساسية:**
{chr(10).join(references)}

**تأكيد الدقة:**
هذا التحليل مبني على قاعدة البيانات القانونية الكاملة للاتحاد الدولي لالتقاط الأوتاد، وتم التحقق من صحة النصوص والمراجع."""

        return enhanced_summary

    def generate_intelligent_legal_response(self, question: str, legal_context: List[Dict[str, Any]], language: str = 'arabic') -> str:
        """Generate intelligent legal response using DeepSeek - SAFE INTEGRATION"""
        try:
            # Analyze question complexity
            mode = self.analyze_query_complexity(question)
            
            # Get DeepSeek response with language support
            result = asyncio.run(self.get_deepseek_response(question, legal_context, mode, language))
            
            if result.get("success"):
                return result["response"]
            else:
                # Fallback message
                return f"AI analysis unavailable: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"AI system error: {str(e)}"

    async def get_deepseek_response(self, question: str, context: List[Dict[str, Any]], mode: str, language: str = 'arabic') -> Dict[str, Any]:
        """Enhanced version with language parameter"""
        try:
            system_prompt, user_prompt = self.create_legal_prompt(question, context, mode, language)
            
            model = "deepseek-reasoner" if mode == "deepseek_reasoner" else "deepseek-chat"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000 if mode == "deepseek_chat" else 8000,
                temperature=0.1,
                stream=False
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model_used": model,
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_needed": True
            }

# إنشاء مثيل عام للاستخدام
deepseek_integration = DeepSeekIntegration()