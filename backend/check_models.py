
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY missing from .env")

client = genai.Client(api_key=api_key)

print("Checking available Gemini models...")

for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print(model.name)
