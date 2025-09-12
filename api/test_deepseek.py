#!/usr/bin/env python3
"""
ITPF - DeepSeek API Test Endpoint
اختبار مباشر لـ DeepSeek API في بيئة Vercel
"""

import json
import os
import requests
from deepseek_simple import deepseek_simple

def handler(event, context):
    """Test handler for DeepSeek integration"""
    try:
        # Test basic integration
        test_question = "اختبار: فريق حصل على 15 نقطة جزاء"
        test_context = [{"title": "اختبار", "content": "قانون الجزاءات في الرياضة"}]
        
        # Call DeepSeek
        result = deepseek_simple.generate_intelligent_legal_response(
            test_question, 
            test_context, 
            "arabic"
        )
        
        # Return test results
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'status': 'test_complete',
                'api_keys_found': len(deepseek_simple.api_keys),
                'current_key': deepseek_simple.current_api_key[:12] + "..." if deepseek_simple.current_api_key else "None",
                'test_question': test_question,
                'deepseek_response': result,
                'response_length': len(result) if result else 0,
                'success': not result.startswith('AI analysis unavailable') if result else False
            }, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'test_failed'
            })
        }

# For direct testing
if __name__ == "__main__":
    result = handler({}, {})
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))