
import os
import httpx
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PlatformAdapter(ABC):
    """Abstract base class for platform adapters"""
    
    @abstractmethod
    def parse_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook data into normalized format.
        Returns dict with:
          - user_id: str
          - message: str
          - metadata: dict
        Returns None if request handled but no message to process (e.g. status update)
        """
        pass

    @abstractmethod
    async def send_message(self, user_id: str, text: str):
        """Send text message back to user"""
        pass

class TelegramAdapter(PlatformAdapter):
    """Adapter for Telegram Bot API"""
    
    def __init__(self, token: str):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"

    def parse_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Telegram update"""
        # We only handle 'message' or 'edited_message' for now
        message = request_data.get('message') or request_data.get('edited_message')
        
        if not message or 'text' not in message:
            return None
            
        user_id = str(message['from']['id'])
        text = message['text']
        username = message['from'].get('username', '')
        first_name = message['from'].get('first_name', '')
        
        return {
            "user_id": user_id,
            "message": text,
            "platform": "telegram",
            "metadata": {
                "username": username,
                "first_name": first_name,
                "chat_id": message['chat']['id']
            }
        }

    async def send_message(self, user_id: str, text: str):
        """Send message via Telegram API"""
        async with httpx.AsyncClient() as client:
            try:
                # user_id in Telegram is the chat_id (for 1:1 chats)
                payload = {
                    "chat_id": user_id,
                    "text": text,
                    "parse_mode": "Markdown"
                }
                response = await client.post(f"{self.api_url}/sendMessage", json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"Error sending Telegram message: {e}")

class WhatsAppAdapter(PlatformAdapter):
    """Adapter for WhatsApp (via Twilio Sandbox)"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.auth = (account_sid, auth_token)
        self.from_number = from_number
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    def parse_request(self, request_data: Any) -> Optional[Dict[str, Any]]:
        """Parse Twilio webhook data (Form-encoded)"""
        # Twilio sends data as dict-like interface (Starlette FormData)
        if not request_data or 'Body' not in request_data:
            return None
            
        body = str(request_data.get('Body', '')).strip()
        from_number = str(request_data.get('From', '')) # e.g. whatsapp:+123456789
        profile_name = str(request_data.get('ProfileName', 'Customer'))
        
        # User ID is the phone number
        user_id = from_number.replace('whatsapp:', '')
        
        return {
            "user_id": user_id,
            "message": body,
            "platform": "whatsapp",
            "metadata": {
                "username": profile_name,
                "phone": user_id
            }
        }

    async def send_message(self, user_id: str, text: str):
        """Send message via Twilio API"""
        async with httpx.AsyncClient() as client:
            try:
                # To: whatsapp:+Number
                to_number = f"whatsapp:{user_id}"
                
                payload = {
                    "To": to_number,
                    "From": self.from_number,
                    "Body": text
                }
                
                response = await client.post(
                    self.api_url, 
                    data=payload, 
                    auth=self.auth
                )
                response.raise_for_status()
            except Exception as e:
                print(f"Error sending WhatsApp message: {e}")

class AdapterFactory:
    @staticmethod
    def get_adapter(platform: str) -> Optional[PlatformAdapter]:
        if platform == "telegram":
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not token:
                print("Warning: TELEGRAM_BOT_TOKEN not set")
                return None
            return TelegramAdapter(token)
            
        if platform == "whatsapp":
            sid = os.getenv("TWILIO_ACCOUNT_SID")
            token = os.getenv("TWILIO_AUTH_TOKEN")
            from_num = os.getenv("TWILIO_FROM_NUMBER", "whatsapp:+14155238886") # Default sandbox
            
            if not sid or not token:
                print("Warning: TWILIO credentials not set")
                return None
            return WhatsAppAdapter(sid, token, from_num)
            
        return None
