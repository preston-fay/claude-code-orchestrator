#!/usr/bin/env python3
"""
Verify Anthropic API key is valid and working.

Usage:
    python scripts/verify_api_key.py
    # or
    ANTHROPIC_API_KEY=sk-ant-... python scripts/verify_api_key.py
"""

import json
import os
import sys
import urllib.request
import urllib.error
import ssl


def verify_api_key(api_key: str | None = None) -> bool:
    """Verify the API key works with Anthropic."""
    
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("\n❌ No API key provided.")
        print("\nSet ANTHROPIC_API_KEY environment variable or pass as argument.")
        print("\nExample:")
        print("  export ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("  python scripts/verify_api_key.py")
        return False
    
    # Validate format
    if not api_key.startswith("sk-ant-"):
        print(f"\n⚠️  API key format looks unusual: {api_key[:10]}...")
        print("   Expected format: sk-ant-api03-...")
    
    print(f"\n🔑 API Key: {api_key[:15]}...{api_key[-4:]}")
    print("\n📡 Testing connection to Anthropic API...")
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    
    payload = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 20,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: OK"
            }
        ]
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        ctx = ssl.create_default_context()
        
        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
            if response.status == 200:
                response_data = json.loads(response.read().decode('utf-8'))
                usage = response_data.get("usage", {})
                
                print("\n✅ API key is valid!")
                print(f"\n   Model: claude-sonnet-4-5-20250929")
                print(f"   Input tokens: {usage.get('input_tokens', 'N/A')}")
                print(f"   Output tokens: {usage.get('output_tokens', 'N/A')}")
                print("\n🎉 You're ready to use the orchestrator with real LLM!")
                print("\n   Run: python scripts/run_workflow_test.py --real-llm")
                return True
            else:
                print(f"\n❌ Unexpected status: {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.code}")
        
        if e.code == 401:
            print("   Invalid API key. Check your key at console.anthropic.com")
        elif e.code == 403:
            print("   API key doesn't have permission for this operation.")
        elif e.code == 429:
            print("   Rate limited. Wait a moment and try again.")
        elif e.code == 500:
            print("   Anthropic server error. Try again later.")
        
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print(f"   Message: {error_body.get('error', {}).get('message', 'Unknown')}")
        except:
            pass
        
        return False
        
    except urllib.error.URLError as e:
        print(f"\n❌ Network Error: {e.reason}")
        print("\n   Check your network connection and firewall settings.")
        print("   The API endpoint is: https://api.anthropic.com")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    # Accept API key as command line argument
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("\n" + "=" * 50)
    print("  Anthropic API Key Verification")
    print("=" * 50)
    
    success = verify_api_key(api_key)
    
    print("\n" + "=" * 50 + "\n")
    
    sys.exit(0 if success else 1)
