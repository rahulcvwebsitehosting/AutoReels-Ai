"""Quick test to diagnose Ollama Cloud API connection."""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OLLAMA_API_KEY", "")
model = os.getenv("OLLAMA_MODEL", "minimax-m3:cloud")
base_url = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/v1")

print(f"  Model:     {model}")
print(f"  Base URL:  {base_url}")
print(f"  API Key:   {'[set]' if api_key else '[MISSING]'}")
print(f"  Key len:   {len(api_key)} chars")
print()

try:
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url)
    print("Sending test request...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
        max_tokens=20,
    )
    choice = response.choices[0]
    print(f"  Finish reason: {choice.finish_reason}")
    print(f"  Content:       {choice.message.content!r}")
    if choice.message.content:
        print("SUCCESS - API works!")
    else:
        print("FAIL - API returned null content")
except Exception as e:
    print(f"FAIL - {type(e).__name__}: {e}")
