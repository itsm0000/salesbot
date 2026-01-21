"""
Brain Module - Main Conversation Processing Engine
منتظر - محرك المحادثة الرئيسي
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local modules
from .personality import PersonalityEngine, PersonalityConfig
from .knowledge import KnowledgeManager

# Import prompt templates
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "data" / "prompts"))
from iraqi_sales import SYSTEM_PROMPT_TEMPLATE


@dataclass
class Message:
    """Single message in a conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    customer_id: str
    platform: str = "manual"  # manual, facebook, whatsapp, etc.
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))

    def get_history_text(self, max_messages: int = 10) -> str:
        """Get conversation history as text"""
        recent = self.messages[-max_messages:]
        history_parts = []
        for msg in recent:
            role_ar = "الزبون" if msg.role == "user" else "أنت"
            history_parts.append(f"{role_ar}: {msg.content}")
        return "\n".join(history_parts)


@dataclass
class BrainResponse:
    """Response from the Brain"""
    response_text: str
    confidence_score: float  # 0.0 - 1.0
    suggested_actions: List[str] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0


class Brain:
    """
    Main reasoning engine for Muntazir.
    Processes customer messages and generates appropriate responses.
    """

    def __init__(
        self,
        personality_config: Optional[PersonalityConfig] = None,
        products_path: Optional[str] = None,
        business_config_path: Optional[str] = None,
    ):
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

        # Initialize components
        self.personality = PersonalityEngine(personality_config)
        self.knowledge = KnowledgeManager(products_path)
        
        # Load business config
        self.business_config = self._load_business_config(business_config_path)
        
        # Active conversations
        self.conversations: Dict[str, ConversationContext] = {}

    def _load_business_config(self, config_path: Optional[str]) -> dict:
        """Load business configuration from JSON"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Default config
        return {
            "business": {
                "name": "بغداد للإنارة",
                "city": "بغداد",
            },
            "policies": {
                "shipping": {"baghdad": 5000, "other_cities": 10000},
                "discounts": {"max_discount_percent": 10},
            },
            "sales_goals": {
                "primary": "بيع المنتج بأفضل سعر"
            }
        }

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context"""
        business = self.business_config.get("business", {})
        policies = self.business_config.get("policies", {})
        shipping = policies.get("shipping", {})
        discounts = policies.get("discounts", {})
        sales_goals = self.business_config.get("sales_goals", {})
        
        personality_context = self.personality.get_system_context()
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            business_name=business.get("name", personality_context["business_name"]),
            city=business.get("city", personality_context["city"]),
            sales_goal=sales_goals.get("primary", "بيع المنتجات وخدمة الزباين"),
            default_honorific=personality_context["default_honorific"],
            max_discount=discounts.get("max_discount_percent", 10),
            product_summary=self.knowledge.get_product_summary(),
            shipping_baghdad=shipping.get("baghdad", 5000),
            shipping_other=shipping.get("other_cities", 10000),
        )

    def get_or_create_conversation(
        self,
        customer_id: str,
        platform: str = "manual"
    ) -> ConversationContext:
        """Get existing conversation or create new one"""
        if customer_id not in self.conversations:
            self.conversations[customer_id] = ConversationContext(
                customer_id=customer_id,
                platform=platform,
            )
        return self.conversations[customer_id]

    async def process_message(
        self,
        message: str,
        customer_id: str,
        platform: str = "manual",
    ) -> BrainResponse:
        """Process a customer message and generate response"""
        import time
        start_time = time.time()

        # Get or create conversation context
        context = self.get_or_create_conversation(customer_id, platform)
        context.add_message("user", message)

        # Build prompt
        system_prompt = self._build_system_prompt()
        conversation_history = context.get_history_text()

        full_prompt = f"""{system_prompt}

المحادثة السابقة:
{conversation_history}

الرد على آخر رسالة من الزبون:"""

        try:
            # Generate response from Gemini
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()

            # Add response to history
            context.add_message("assistant", response_text)

            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)
            confidence = self._calculate_confidence(response_text)

            return BrainResponse(
                response_text=response_text,
                confidence_score=confidence,
                suggested_actions=self._detect_actions(response_text, message),
                flags=self._detect_flags(message, response_text),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            print(f"Error generating response: {e}")
            # Return a safe fallback response
            fallback = "عذراً حجي، صار خطأ تقني. دقيقة وأرد عليك..."
            return BrainResponse(
                response_text=fallback,
                confidence_score=0.1,
                flags={"error": str(e)},
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    def process_message_sync(
        self,
        message: str,
        customer_id: str,
        platform: str = "manual",
    ) -> BrainResponse:
        """Synchronous version of process_message"""
        import time
        start_time = time.time()

        # Get or create conversation context
        context = self.get_or_create_conversation(customer_id, platform)
        context.add_message("user", message)

        # Build prompt
        system_prompt = self._build_system_prompt()
        conversation_history = context.get_history_text()

        full_prompt = f"""{system_prompt}

المحادثة السابقة:
{conversation_history}

الرد على آخر رسالة من الزبون:"""

        try:
            # Generate response from Gemini
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()

            # Add response to history
            context.add_message("assistant", response_text)

            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)
            confidence = self._calculate_confidence(response_text)

            return BrainResponse(
                response_text=response_text,
                confidence_score=confidence,
                suggested_actions=self._detect_actions(response_text, message),
                flags=self._detect_flags(message, response_text),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            print(f"Error generating response: {e}")
            fallback = "عذراً حجي، صار خطأ تقني. دقيقة وأرد عليك..."
            return BrainResponse(
                response_text=fallback,
                confidence_score=0.1,
                flags={"error": str(e)},
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

    def _calculate_confidence(self, response: str) -> float:
        """Calculate confidence score for the response"""
        # Simple heuristics for now
        confidence = 0.7  # Base confidence

        # Lower confidence for short responses
        if len(response) < 20:
            confidence -= 0.1

        # Lower confidence for uncertain phrases
        uncertain_phrases = ["ما أعرف", "مو متأكد", "خلني أسأل", "دقيقة"]
        for phrase in uncertain_phrases:
            if phrase in response:
                confidence -= 0.15

        # Higher confidence for product mentions
        for product in self.knowledge.products.values():
            if product.name in response:
                confidence += 0.1
                break

        return max(0.1, min(1.0, confidence))

    def _detect_actions(self, response: str, message: str) -> List[str]:
        """Detect suggested follow-up actions"""
        actions = []

        # Detect pricing inquiry
        if any(word in message for word in ["سعر", "چم", "كم", "بكم"]):
            actions.append("pricing_inquiry")

        # Detect potential sale
        if any(word in response for word in ["عنوان", "توصيل", "رقم"]):
            actions.append("potential_sale")

        # Detect negotiation
        if any(word in message for word in ["غالي", "خصم", "تخفيض", "آخر سعر"]):
            actions.append("negotiation")

        return actions

    def _detect_flags(self, message: str, response: str) -> Dict[str, Any]:
        """Detect flags that might need attention"""
        flags = {}

        # Flag complaints
        complaint_words = ["مشكلة", "شكوى", "زين", "خربان", "مرجوع"]
        if any(word in message for word in complaint_words):
            flags["complaint_detected"] = True

        # Flag if asking about unavailable product
        if "غير متوفر" in response or "نفذ" in response:
            flags["out_of_stock_query"] = True

        return flags

    def clear_conversation(self, customer_id: str):
        """Clear conversation history for a customer"""
        if customer_id in self.conversations:
            del self.conversations[customer_id]

    def get_conversation_summary(self, customer_id: str) -> str:
        """Get a summary of the conversation"""
        if customer_id not in self.conversations:
            return "لا توجد محادثة"
        
        context = self.conversations[customer_id]
        return f"عدد الرسائل: {len(context.messages)}, المنصة: {context.platform}"
