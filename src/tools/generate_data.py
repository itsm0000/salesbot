
import os
import json
import time
import random
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict

# Force UTF-8 for Windows console
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-flash-latest")

OUTPUT_FILE = Path("data/conversations/raw_examples.json")
TARGET_COUNT = 10  # Start with 10 for testing, aim for 50 later

# Scenarios to generate
SCENARIOS = [
    "customer asks about smart bulb price and tries to negotiate",
    "customer asks for a discount on a large order of strip lights",
    "customer complains about a previous broken item",
    "customer asks if the product is original (asli) or commercial",
    "customer wants recommendations for a living room (sola)",
    "customer asks about delivery to Basra",
]

PROMPT_TEMPLATE = """
Generate a realistic short conversation (3-5 turns) between an Iraqi customer and a sales agent named "Muntazir" for a lighting shop in Baghdad.
Use **authentic Iraqi Arabic dialect** (Baghdadi). 
Scenario: {scenario}

Format the output strictly as a JSON array of objects, where each object has "role" (user/assistant) and "content" (Arabic text).
Example:
[
    {{"role": "user", "content": "السلام عليكم، بيش هذا المصباح؟"}},
    {{"role": "assistant", "content": "وعليكم السلام حجي، هذا بـ 5000 دينار."}}
]
"""

def generate_conversation(scenario: str) -> List[Dict[str, str]]:
    prompt = PROMPT_TEMPLATE.format(scenario=scenario)
    try:
        # Use simple text generation and strip code blocks if present
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up Markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text.strip())
    except Exception as e:
        print(f"Error generating scenario '{scenario}': {e}")
        return []

def main():
    print(f"🚀 Starting data generation... Target: {TARGET_COUNT} conversations")
    
    existing_data = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                pass
    
    new_conversations = []
    
    for i in range(TARGET_COUNT):
        scenario = random.choice(SCENARIOS)
        print(f"[{i+1}/{TARGET_COUNT}] Generating: {scenario}...")
        
        conv = generate_conversation(scenario)
        if conv:
            entry = {
                "id": f"conv_{int(time.time())}_{i}",
                "scenario": scenario,
                "timestamp": time.time(),
                "messages": conv
            }
            new_conversations.append(entry)
            # Sleep briefly to avoid rate limits if any
            time.sleep(1)
    
    # Save results
    all_data = existing_data + new_conversations
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Generated {len(new_conversations)} new conversations.")
    print(f"📁 Total saved: {len(all_data)} in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
