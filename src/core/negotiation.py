
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any

@dataclass
class Negotiationstate:
    product_id: str
    original_price: float
    current_offer: float
    round_count: int = 0
    is_active: bool = True
    min_acceptable_price: float = 0.0

class NegotiationEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Default policy: Max 15% discount
        self.max_discount_percent = self.config.get("max_discount_percent", 15)
        # Steps for discount offering (e.g., 5% then 10% then 15%)
        self.discount_steps = [0.05, 0.10, 0.15]

    def start_negotiation(self, product_id: str, price: float) -> Negotiationstate:
        """Initialize negotiation for a product"""
        min_price = price * (1 - (self.max_discount_percent / 100))
        return Negotiationstate(
            product_id=product_id,
            original_price=price,
            current_offer=price,
            min_acceptable_price=min_price
        )

    def process_offer(self, state: Negotiationstate, customer_offer: Optional[float] = None) -> Tuple[str, float]:
        """
        Process a customer's haggle attempt.
        Returns (response_key, new_price)
        """
        state.round_count += 1
        
        # If customer offers a specific price
        if customer_offer:
            if customer_offer >= state.min_acceptable_price:
                state.current_offer = customer_offer
                state.is_active = False # Deal accepted
                return "accept_customer_offer", customer_offer
            else:
                # Counter offer
                return self._make_counter_offer(state)
        
        # If just asking for "lower price" without number
        return self._make_counter_offer(state)

    def _make_counter_offer(self, state: Negotiationstate) -> Tuple[str, float]:
        """Calculate the next counter offer"""
        step_index = min(state.round_count - 1, len(self.discount_steps) - 1)
        discount_percent = self.discount_steps[step_index]
        
        new_price = state.original_price * (1 - discount_percent)
        
        # Round to nearest 1000 or 500 for clean numbers
        new_price = round(new_price / 250) * 250
        
        if new_price < state.min_acceptable_price:
            new_price = state.min_acceptable_price

        state.current_offer = new_price
        
        if step_index == len(self.discount_steps) - 1:
            return "final_offer", new_price
            
        return "counter_offer", new_price

    def get_response_prompt(self, response_key: str, price: float, original: float) -> str:
        """Get the prompt instruction for the LLM based on negotiation result"""
        prompts = {
            "accept_customer_offer": f"وافق على السعر {price:,.0f} دينار بحماس. قول 'مبروك عليك'.",
            "counter_offer": f"الزبون يريد تخفيض. قدم عرض جديد بـ {price:,.0f} دينار. السعر الاصلي جان {original:,.0f}. قول 'لخاطرك' أو 'تستاهل'.",
            "final_offer": f"هذا آخر سعر {price:,.0f} دينار. اعتذر بلطف وقول ما اكدر انزل بعد. (قفل السعر).",
            "reject_low": f"السعر المعروض قليل جداً. ارفض بلطف واشرح جودة المنتج."
        }
        return prompts.get(response_key, "")
