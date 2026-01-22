
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.brain import Brain

# Force UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def main():
    print("🚀 Initializing Brain for Negotiation Test...")
    brain = Brain(
        products_path="data/products.csv",
        business_config_path="config/business_config.json"
    )
    
    customer_id = "test_user_neg_1"
    
    # Sequence of messages
    scenario = [
        "السلام عليكم، بيش المصباح الذكي RGB؟",  # Should trigger product detection
        "25 ألف هواي، ما ترهم بـ 20؟",          # Should trigger negotiation & counter offer (maybe 24k)
        "بعده غالي، سويلي ياه بـ 22",           # Should trigger 2nd counter offer (maybe 23k or accept)
        "ماشي اتفقنا على السعر"                 # Recognition of agreement
    ]
    
    print("-" * 50)
    
    for i, msg in enumerate(scenario):
        print(f"\n👤 User: {msg}")
        response = await brain.process_message(msg, customer_id)
        
        print(f"🤖 Bot: {response.response_text}")
        
        # Inspect internals
        context = brain.conversations.get(customer_id)
        if context:
            neg_state = context.metadata.get("negotiation_state")
            prod_id = context.metadata.get("current_product_id")
            if neg_state:
                print(f"   [State: Round {neg_state.round_count}, Offer {neg_state.current_offer}, Min {neg_state.min_acceptable_price}]")
            else:
                print(f"   [State: No active negotiation, Product: {prod_id}]")

if __name__ == "__main__":
    asyncio.run(main())
