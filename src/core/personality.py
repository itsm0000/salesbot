"""
Personality Engine - Iraqi Arabic Tone & Style Management
منتظر - محرك الشخصية العراقية
"""

import random
from typing import Optional
from dataclasses import dataclass


@dataclass
class PersonalityConfig:
    """Configuration for the AI persona"""
    business_name: str = "بغداد للإنارة"
    city: str = "بغداد"
    formality_level: int = 3  # 1-5: Street vendor to corporate
    emoji_usage: int = 30  # 0-100%
    negotiation_aggressiveness: int = 3  # 1-5
    default_honorific: str = "حجي"
    response_delay_min: int = 2
    response_delay_max: int = 8


class PersonalityEngine:
    """
    Manages the Iraqi Arabic persona for the sales agent.
    Handles honorifics, tone, and cultural nuances.
    """

    # Honorifics based on context/relationship
    HONORIFICS = {
        "elder_male": ["حجي", "عمو", "أبو"],
        "peer_male": ["اخوي", "صديقي", "خوش"],
        "formal_male": ["استاذ", "سيد"],
        "elder_female": ["حجية", "خالة", "عمة"],
        "peer_female": ["اختي", "صديقتي"],
        "formal_female": ["استاذة", "ست"],
        "neutral": ["صديقي", "عزيزي"],
    }

    # Common Iraqi expressions
    EXPRESSIONS = {
        "agreement": ["زين", "تمام", "أي والله", "صحيح", "هيچي"],
        "emphasis": ["والله", "بالله", "صدق", "أكيد"],
        "thinking": ["دقيقة", "لحظة", "خلني أشوف"],
        "appreciation": ["يسلمو", "مشكور", "الله يخليك", "تسلم"],
        "surprise": ["واو", "والله!", "شدعوة", "هاي شنو"],
    }

    # Emojis appropriate for Iraqi sales context
    SALES_EMOJIS = ["👍", "✨", "🔥", "💡", "⭐", "🎯", "💪", "🤝", "❤️", "👌"]

    def __init__(self, config: Optional[PersonalityConfig] = None):
        self.config = config or PersonalityConfig()

    def get_honorific(self, context: str = "neutral") -> str:
        """Get appropriate honorific based on context"""
        honorifics = self.HONORIFICS.get(context, self.HONORIFICS["neutral"])
        
        # Use default more often for consistency
        if random.random() < 0.7:
            return self.config.default_honorific
        return random.choice(honorifics)

    def add_expression(self, expression_type: str) -> str:
        """Add a natural Iraqi expression"""
        expressions = self.EXPRESSIONS.get(expression_type, [])
        if expressions:
            return random.choice(expressions)
        return ""

    def should_add_emoji(self) -> bool:
        """Decide whether to add emoji based on config"""
        return random.randint(1, 100) <= self.config.emoji_usage

    def get_emoji(self) -> str:
        """Get a random appropriate emoji"""
        if self.should_add_emoji():
            return random.choice(self.SALES_EMOJIS)
        return ""

    def get_response_delay(self) -> int:
        """Get human-like response delay in seconds"""
        return random.randint(
            self.config.response_delay_min,
            self.config.response_delay_max
        )

    def format_price(self, price: int) -> str:
        """Format price in Iraqi style"""
        if price >= 1000:
            # Format with commas for readability
            formatted = f"{price:,}".replace(",", "،")
            return f"{formatted} دينار"
        return f"{price} دينار"

    def get_greeting(self, time_of_day: str = "day") -> str:
        """Get appropriate greeting based on time"""
        greetings = {
            "morning": ["صباح الخير", "صباح النور", "صباحو"],
            "day": ["هلا والله", "أهلين", "مرحبا", "هلا"],
            "evening": ["مساء الخير", "مساء النور", "مساءكم خير"],
        }
        return random.choice(greetings.get(time_of_day, greetings["day"]))

    def get_farewell(self) -> str:
        """Get appropriate farewell"""
        farewells = [
            "مع السلامة",
            "الله وياك",
            "تشرفنا",
            "إن شاء الله نشوفك",
            "سلامات",
        ]
        return random.choice(farewells)

    def adjust_formality(self, text: str) -> str:
        """Adjust text formality based on config level"""
        # For now, return as-is. Future: transform formal ↔ casual
        return text

    def get_system_context(self) -> dict:
        """Get personality context for prompt injection"""
        return {
            "business_name": self.config.business_name,
            "city": self.config.city,
            "default_honorific": self.config.default_honorific,
            "formality_level": self.config.formality_level,
            "max_discount": self._get_max_discount(),
        }

    def _get_max_discount(self) -> int:
        """Get max discount based on negotiation aggressiveness"""
        # Lower aggressiveness = higher willingness to discount
        discount_map = {1: 15, 2: 12, 3: 10, 4: 7, 5: 5}
        return discount_map.get(self.config.negotiation_aggressiveness, 10)
