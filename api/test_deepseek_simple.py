#!/usr/bin/env python3
"""
Simple DeepSeek Test - Direct API Test
"""

import json
import os

def handler(event, context):
    """Simple test handler for DeepSeek"""
    try:
        # Import here to avoid startup issues
        from deepseek_simple import deepseek_simple
        
        # Test question
        test_question = "فريق حصل على 15 نقطة جزاء، ما الحكم القانوني؟"
        test_context = [{"title": "قانون الجزاءات", "content": "تطبق قوانين الجزاء حسب عدد النقاط"}]
        
        # Get response
        ai_response = deepseek_simple.generate_intelligent_legal_response(
            test_question, test_context, "arabic"
        )
        
        # Check if it's really AI or template
        is_ai_response = not ai_response.startswith('AI analysis unavailable')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json; charset=utf-8',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'status': 'test_complete',
                'deepseek_available': len(deepseek_simple.api_keys) > 0,
                'current_api_key': deepseek_simple.current_api_key[:12] + "..." if deepseek_simple.current_api_key else "None",
                'ai_response': ai_response,
                'is_real_ai': is_ai_response,
                'response_length': len(ai_response),
                'env_keys': {
                    'DEEPSEEK_API_KEY': 'found' if os.environ.get('DEEPSEEK_API_KEY') else 'missing',
                    'DEEPSEEK_API_KEY_1': 'found' if os.environ.get('DEEPSEEK_API_KEY_1') else 'missing',
                    'DEEPSEEK_API_KEY_2': 'found' if os.environ.get('DEEPSEEK_API_KEY_2') else 'missing',
                    'DEEPSEEK_API_KEY_3': 'found' if os.environ.get('DEEPSEEK_API_KEY_3') else 'missing',
                }
            }, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'status': 'test_failed'
            })
        }

if __name__ == "__main__":
    result = handler({}, {})
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))