import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {bool(api_key)}")

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("Testing gemini-1.5-flash...")
    response = model.generate_content("Say Hello in English")
    print("Response:", response.text)
except Exception as e:
    print(f"Error with gemini-1.5-flash: {e}")

try:
    model = genai.GenerativeModel("models/gemini-flash-latest")
    print("Testing models/gemini-flash-latest...")
    response = model.generate_content("Say Hello in English")
    print("Response:", response.text)
except Exception as e:
    print(f"Error with models/gemini-flash-latest: {e}")
