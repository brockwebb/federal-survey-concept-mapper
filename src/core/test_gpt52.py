#!/usr/bin/env python3
"""
Smoke test for gpt-5.2 model availability.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("Testing gpt-5.2 variants...")

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

variants = [
    "gpt-5.2",
    "gpt-5-2", 
    "gpt-5.2-turbo",
    "gpt-5",
]

for model_name in variants:
    try:
        print(f"\nTrying: {model_name}")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say hello"}],
            max_completion_tokens=10
        )
        print(f"  ✓ SUCCESS: {response.choices[0].message.content}")
        print(f"  ** USE THIS ONE: {model_name} **")
        break
    except Exception as e:
        print(f"  ✗ Failed: {e}")

print("\nDone!")
