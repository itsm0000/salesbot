
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from core.brain import Brain

def test_prompt_building():
    print("Testing Brain prompt building...")
    
    # Mock config
    os.environ["GEMINI_API_KEY"] = "dummy_key"
    
    brain = Brain()
    
    # Test 1: Default
    prompt_default = brain._build_system_prompt(customer_name="Ali")
    print("\n--- Prompt (Default) ---")
    if "{customer_name}" in prompt_default or "{target_audience}" in prompt_default:
        print("FAIL: Placeholders not filled")
    else:
        print("SUCCESS: Placeholders filled")
        
    if "Ali" in prompt_default:
         print("SUCCESS: Customer name present")
         
    # Test 2: Custom Audience
    brain.business_config["target_audience"] = "رياضيين وشباب"
    brain.business_config["business"]["default_honorific"] = "كابتن"
    
    prompt_custom = brain._build_system_prompt(customer_name="Zahra")
    print("\n--- Prompt (Custom) ---")
    if "رياضيين وشباب" in prompt_custom:
         print("SUCCESS: Target audience present")
    if "كابتن" in prompt_custom:
         print("SUCCESS: Default honorific updated")
         
    print("\nDone.")

if __name__ == "__main__":
    try:
        test_prompt_building()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
