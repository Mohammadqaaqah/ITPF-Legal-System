#!/usr/bin/env python3
"""
DeepSeek API Test and Diagnostic Tool
أداة اختبار وتشخيص DeepSeek API
"""

import os
import sys
import requests
import json
from typing import Dict, Any, List

class DeepSeekTester:
    """أداة اختبار شاملة لـ DeepSeek API"""
    
    def __init__(self):
        self.base_url = "https://api.deepseek.com"
        self.api_keys = []
        self.load_api_keys()
    
    def load_api_keys(self):
        """تحميل جميع مفاتيح API الممكنة"""
        potential_keys = [
            os.getenv('DEEPSEEK_API_KEY'),
            os.getenv('DEEPSEEK_API_KEY_1'),
            os.getenv('DEEPSEEK_API_KEY_2'),
            os.getenv('DEEPSEEK_API_KEY_3')
        ]
        
        for key in potential_keys:
            if key and len(key) > 10 and not key.startswith('your-actual'):
                self.api_keys.append(key)
                print(f"🔑 Found API key: {key[:8]}...{key[-4:]}")
        
        if not self.api_keys:
            print("⚠️ No API keys found in environment variables!")
            print("Available environment variables:")
            for var in os.environ:
                if 'DEEPSEEK' in var:
                    print(f"  {var} = {os.environ[var][:10]}...")
    
    def test_api_key(self, api_key: str) -> Dict[str, Any]:
        """اختبار مفتاح API واحد"""
        print(f"\n🧪 Testing API key: {api_key[:8]}...{api_key[-4:]}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "Hello, test message"}
            ],
            "max_tokens": 10,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            print(f"📡 Response status: {response.status_code}")
            print(f"📡 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS: API key is valid")
                print(f"Model used: {result.get('model', 'unknown')}")
                print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', '')}")
                return {"success": True, "response": result}
            
            elif response.status_code == 401:
                error_data = response.json() if response.content else {}
                print(f"❌ AUTHENTICATION FAILED: {error_data}")
                return {"success": False, "error": "401 Authentication Failed", "details": error_data}
            
            elif response.status_code == 402:
                print("❌ INSUFFICIENT BALANCE: Need to add funds")
                return {"success": False, "error": "402 Insufficient Balance"}
            
            else:
                error_data = response.json() if response.content else {}
                print(f"❌ ERROR {response.status_code}: {error_data}")
                return {"success": False, "error": f"HTTP {response.status_code}", "details": error_data}
                
        except requests.exceptions.RequestException as e:
            print(f"❌ NETWORK ERROR: {str(e)}")
            return {"success": False, "error": "Network Error", "details": str(e)}
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {str(e)}")
            return {"success": False, "error": "Unexpected Error", "details": str(e)}
    
    def test_all_keys(self) -> List[Dict[str, Any]]:
        """اختبار جميع مفاتيح API المتاحة"""
        print("🚀 Starting comprehensive DeepSeek API test")
        print(f"Found {len(self.api_keys)} API keys to test")
        
        results = []
        for i, key in enumerate(self.api_keys, 1):
            print(f"\n{'='*50}")
            print(f"Testing key {i}/{len(self.api_keys)}")
            result = self.test_api_key(key)
            results.append({"key_index": i, "key": f"{key[:8]}...{key[-4:]}", **result})
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """إنتاج تقرير شامل"""
        print(f"\n{'='*70}")
        print("🔍 DEEPSEEK API DIAGNOSTIC REPORT")
        print(f"{'='*70}")
        
        working_keys = [r for r in results if r.get('success')]
        failed_keys = [r for r in results if not r.get('success')]
        
        print(f"✅ Working keys: {len(working_keys)}")
        print(f"❌ Failed keys: {len(failed_keys)}")
        
        if working_keys:
            print("\n🟢 WORKING API KEYS:")
            for result in working_keys:
                print(f"  - Key {result['key_index']}: {result['key']}")
        
        if failed_keys:
            print("\n🔴 FAILED API KEYS:")
            for result in failed_keys:
                print(f"  - Key {result['key_index']}: {result['key']}")
                print(f"    Error: {result.get('error', 'Unknown')}")
                if 'details' in result:
                    print(f"    Details: {result['details']}")
        
        # Recommendations
        print(f"\n{'='*50}")
        print("💡 RECOMMENDATIONS:")
        
        if working_keys:
            print("✅ At least one API key is working - DeepSeek integration should be functional")
            print(f"✅ Use key {working_keys[0]['key_index']} as primary")
        else:
            print("❌ No working API keys found!")
            print("🔧 Actions needed:")
            print("   1. Check API key validity at https://platform.deepseek.com/api_keys")
            print("   2. Generate new API keys if needed")
            print("   3. Verify account balance at https://platform.deepseek.com/")
            print("   4. Update environment variables on Vercel")
        
        return len(working_keys) > 0

def main():
    """تشغيل الاختبار الرئيسي"""
    tester = DeepSeekTester()
    
    if not tester.api_keys:
        print("❌ No API keys available for testing!")
        print("Please set environment variables: DEEPSEEK_API_KEY, DEEPSEEK_API_KEY_1, etc.")
        return False
    
    results = tester.test_all_keys()
    success = tester.generate_report(results)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)