#!/usr/bin/env python3
"""
ITPF Legal System - Simplified DeepSeek Integration
تكامل مبسط وفعال مع DeepSeek API
"""

import json
import os
import requests
from typing import Dict, Any, List, Optional

class SimpleDeepSeekIntegration:
    """تكامل مبسط مع DeepSeek API"""
    
    def __init__(self):
        """تهيئة النظام"""
        self.api_keys = []
        self.current_key_index = 0
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
        # جمع مفاتيح API
        potential_keys = ['DEEPSEEK_API_KEY', 'DEEPSEEK_API_KEY_1', 'DEEPSEEK_API_KEY_2', 'DEEPSEEK_API_KEY_3']
        
        for key_name in potential_keys:
            value = os.environ.get(key_name)
            if value and len(value) > 20:
                self.api_keys.append(value)
                print(f"🔑 DeepSeek Key Found: {key_name}")
        
        print(f"📊 Total DeepSeek API Keys: {len(self.api_keys)}")
        
        # تعيين المفتاح الحالي
        self.current_api_key = self.api_keys[0] if self.api_keys else None
        
        if not self.current_api_key:
            print("❌ No valid DeepSeek API keys found!")
        else:
            print(f"✅ Using API key: {self.current_api_key[:12]}...")
    
    def generate_intelligent_legal_response(self, question: str, legal_context: List[Dict[str, Any]], language: str = 'arabic') -> str:
        """Generate intelligent response using DeepSeek"""
        
        if not self.current_api_key:
            return "AI analysis unavailable: No API keys configured"
        
        try:
            # إعداد السياق القانوني
            context_text = ""
            for item in legal_context[:5]:  # أول 5 مراجع فقط
                context_text += f"• {item.get('title', 'مادة قانونية')}: {item.get('content', '')[:200]}...\n"
            
            # إعداد النظام
            system_prompt = """أنت خبير قانوني متخصص في قوانين الاتحاد الدولي لالتقاط الأوتاد (ITPF). 
            مهمتك تحليل السؤال القانوني بعمق وتقديم إجابة ذكية ومحددة بناءً على القوانين المتاحة.
            
            تعليمات مهمة:
            1. حلل السؤال بدقة وقدم إجابة محددة للسيناريو المطروح
            2. استخدم المراجع القانونية المتاحة
            3. تجنب الإجابات العامة
            4. قدم تحليل قانوني عملي
            5. أجب باللغة المطلوبة (عربي/إنجليزي)"""
            
            # إعداد الطلب
            user_prompt = f"""السؤال القانوني: {question}

المراجع القانونية المتاحة:
{context_text}

المطلوب: تحليل قانوني محدد وعملي للسيناريو المطروح في السؤال."""

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
                "Authorization": f"Bearer {self.current_api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"🚀 Calling DeepSeek API...")
            
            # إرسال الطلب
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            
            print(f"📊 DeepSeek Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content']
                    print(f"✅ DeepSeek Success: {len(ai_response)} chars")
                    return ai_response
                else:
                    print(f"❌ No choices in response: {result}")
                    return "AI analysis unavailable: Invalid response format"
            else:
                error_text = response.text
                print(f"❌ API Error {response.status_code}: {error_text}")
                return f"AI analysis unavailable: API Error {response.status_code}"
                
        except Exception as e:
            print(f"❌ DeepSeek Exception: {str(e)}")
            return f"AI analysis unavailable: {str(e)}"

# إنشاء المثيل العالمي
deepseek_simple = SimpleDeepSeekIntegration()

# للاختبار المحلي
if __name__ == "__main__":
    test_question = "فريق حصل على 15 نقطة جزاء، ما وضعه القانوني؟"
    test_context = [{"title": "قانون الجزاءات", "content": "تطبق الجزاءات حسب عدد النقاط المحققة"}]
    
    result = deepseek_simple.generate_intelligent_legal_response(test_question, test_context, "arabic")
    print(f"🔍 Test Result: {result}")