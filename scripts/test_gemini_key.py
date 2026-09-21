import os
import sys
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")

print("=" * 50)
print("EviBite AI - Gemini API Key Diagnostic")
print("=" * 50)

if not api_key:
    print("[ERROR] No GEMINI_API_KEY found in your .env file!")
    print("Please add your key to the .env file as:")
    print("GEMINI_API_KEY=AIzaSy...")
    sys.exit(1)

masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
print(f"[INFO] Found API Key in .env: {masked_key}")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("[ERROR] 'google-genai' package is not installed.")
    print("Please install it by running: pip install google-genai")
    sys.exit(1)

models_to_test = [
    os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-flash-latest"
]

models_to_test = list(dict.fromkeys([m for m in models_to_test if m]))

print(f"\nTesting connection to Gemini API...")

success = False
for model_name in models_to_test:
    print(f"\nTesting model: '{model_name}'...")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'Gemini API Key is working successfully!'",
            config=types.GenerateContentConfig(temperature=0.1)
        )
        if response.text:
            print(f"[SUCCESS] Model '{model_name}' responded!")
            print(f"   Response from Gemini: {response.text.strip()}")
            success = True
            break
    except Exception as e:
        print(f"[FAILED] Model '{model_name}': {e}")

print("\n" + "=" * 50)
if success:
    print("SUCCESS: Your Gemini API Key is ACTIVE and WORKING PERFECTLY!")
else:
    print("ERROR: API Key test failed. Please check your API key or permissions.")
print("=" * 50)

