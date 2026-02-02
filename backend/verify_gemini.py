import google.generativeai as genai
from google.generativeai.types import GenerationConfig

print(f"Version: {genai.__version__}")

try:
    config = GenerationConfig(response_mime_type="application/json")
    print("GenerationConfig accepts response_mime_type: YES")
except TypeError:
    print("GenerationConfig accepts response_mime_type: NO")
except Exception as e:
    print(f"Other error: {e}")
