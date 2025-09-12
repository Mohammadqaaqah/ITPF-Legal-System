#!/usr/bin/env python3
"""
Debug endpoint to check DeepSeek API integration status
نقطة تشخيص لفحص حالة تكامل DeepSeek API
"""

import json
import os
from deepseek_integration import deepseek_integration

def handler(event, context):
    """Debug handler for Vercel"""
    try:
        # Check environment variables
        env_info = {}
        for key in os.environ.keys():
            if any(keyword in key.upper() for keyword in ['DEEP', 'API', 'KEY']):
                value = os.environ[key]
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "short_value"
                env_info[key] = masked_value
        
        # Check API keys in integration
        api_keys_info = {
            "total_keys": len(deepseek_integration.api_keys),
            "current_key_index": deepseek_integration.current_key_index,
            "current_api_key": f"{deepseek_integration.current_api_key[:8]}...{deepseek_integration.current_api_key[-4:]}" if deepseek_integration.current_api_key and len(deepseek_integration.current_api_key) > 12 else str(deepseek_integration.current_api_key),
            "base_url": deepseek_integration.base_url
        }
        
        # Test a simple API call
        test_result = None
        try:
            test_result = deepseek_integration.generate_intelligent_legal_response(
                question="Test question",
                legal_context=[],
                language="english"
            )
        except Exception as e:
            test_result = f"Test failed: {str(e)}"
        
        debug_info = {
            "status": "debug_active",
            "environment_variables": env_info,
            "api_keys_info": api_keys_info,
            "test_result": test_result,
            "integration_loaded": deepseek_integration is not None
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(debug_info, ensure_ascii=False, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': json.dumps({
                'error': str(e),
                'status': 'debug_failed'
            })
        }

# For direct testing
if __name__ == "__main__":
    result = handler({}, {})
    print(json.dumps(json.loads(result['body']), indent=2, ensure_ascii=False))