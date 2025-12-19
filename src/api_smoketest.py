#!/usr/bin/env python3
"""
Simple smoke test for API connectivity.
"""

import os
from dotenv import load_dotenv
import anthropic
from openai import OpenAI

load_dotenv()

print("="*70)
print("API CONNECTIVITY SMOKE TEST")
print("="*70)

# Test OpenAI
print("\n1. Testing OpenAI API...")
try:
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("  ❌ No OPENAI_API_KEY in .env")
    else:
        print(f"  ✓ Key found: {openai_key[:10]}...")
        
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": "What is 2+2? Answer with just the number."}],
            max_completion_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"  ✓ Response: {result}")
        print(f"  ✓ OpenAI API working!")
        
except Exception as e:
    print(f"  ❌ OpenAI Error: {e}")

# Test Claude
print("\n2. Testing Claude API...")
try:
    claude_key = os.getenv('ANTHROPIC_API_KEY')
    if not claude_key:
        print("  ❌ No ANTHROPIC_API_KEY in .env")
    else:
        print(f"  ✓ Key found: {claude_key[:10]}...")
        
        client = anthropic.Anthropic(api_key=claude_key)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=50,
            messages=[{"role": "user", "content": "What is 2+2? Answer with just the number."}]
        )
        
        result = response.content[0].text
        print(f"  ✓ Response: {result}")
        print(f"  ✓ Claude API working!")
        
except Exception as e:
    print(f"  ❌ Claude Error: {e}")

print("\n" + "="*70)
print("SMOKE TEST COMPLETE")
print("="*70)
