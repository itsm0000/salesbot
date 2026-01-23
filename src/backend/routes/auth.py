"""
Authentication routes - Phone number login via Telegram
"""
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session, Business

router = APIRouter()

# Telegram API credentials
API_ID = os.getenv("TELEGRAM_API_ID", "30619302")
API_HASH = os.getenv("TELEGRAM_API_HASH", "a501dc4dd3e7e2288cdc3dc18ff9e3ce")

# Temporary storage for pending logins (in production, use Redis)
_pending_logins: dict[str, TelegramClient] = {}


class RequestCodeRequest(BaseModel):
    phone: str


class RequestCodeResponse(BaseModel):
    success: bool
    phone_code_hash: Optional[str] = None
    message: str


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str
    phone_code_hash: str
    business_name: str
    business_city: Optional[str] = None


class VerifyCodeResponse(BaseModel):
    success: bool
    business_id: Optional[int] = None
    message: str


class BusinessInfo(BaseModel):
    id: int
    phone: str
    name: str
    city: Optional[str]
    is_active: bool
    telegram_id: Optional[int]


@router.post("/request-code", response_model=RequestCodeResponse)
async def request_code(request: RequestCodeRequest):
    """
    Step 1: Request a verification code to be sent to the phone number.
    """
    phone = request.phone.strip()
    
    # Normalize phone number
    if not phone.startswith("+"):
        if phone.startswith("964"):
            phone = "+" + phone
        elif phone.startswith("0"):
            phone = "+964" + phone[1:]
        else:
            phone = "+964" + phone
    
    try:
        # Create a new client for this login
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        
        # Request the code
        result = await client.send_code_request(phone)
        
        # Store client for verification step
        _pending_logins[phone] = client
        
        return RequestCodeResponse(
            success=True,
            phone_code_hash=result.phone_code_hash,
            message="تم إرسال رمز التحقق إلى التلغرام"
        )
        
    except Exception as e:
        print(f"Error requesting code: {e}")
        return RequestCodeResponse(
            success=False,
            message=f"خطأ: {str(e)}"
        )


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(request: VerifyCodeRequest):
    """
    Step 2: Verify the code and create/update business account.
    """
    phone = request.phone.strip()
    
    # Normalize phone
    if not phone.startswith("+"):
        if phone.startswith("964"):
            phone = "+" + phone
        elif phone.startswith("0"):
            phone = "+964" + phone[1:]
        else:
            phone = "+964" + phone
    
    # Get pending client
    client = _pending_logins.get(phone)
    if not client:
        raise HTTPException(status_code=400, detail="جلسة التحقق منتهية، أعد المحاولة")
    
    try:
        # Sign in with the code
        await client.sign_in(
            phone=phone,
            code=request.code,
            phone_code_hash=request.phone_code_hash
        )
        
        # Get user info
        me = await client.get_me()
        
        # Save session string
        session_string = client.session.save()
        
        # Clean up pending login
        del _pending_logins[phone]
        
        # Create or update business in database
        async with async_session() as session:
            # Check if business exists
            result = await session.execute(
                select(Business).where(Business.phone == phone)
            )
            business = result.scalar_one_or_none()
            
            if business:
                # Update existing
                business.session_string = session_string
                business.telegram_id = me.id
                business.name = request.business_name
                if request.business_city:
                    business.city = request.business_city
            else:
                # Create new
                business = Business(
                    phone=phone,
                    name=request.business_name,
                    city=request.business_city,
                    telegram_id=me.id,
                    session_string=session_string,
                    is_active=False  # Not active until they start the bot
                )
                session.add(business)
            
            await session.commit()
            await session.refresh(business)
            
            return VerifyCodeResponse(
                success=True,
                business_id=business.id,
                message="تم تسجيل الدخول بنجاح!"
            )
        
    except Exception as e:
        print(f"Error verifying code: {e}")
        
        # Check if it's a password requirement (2FA)
        if "password" in str(e).lower():
            return VerifyCodeResponse(
                success=False,
                message="حسابك محمي بكلمة مرور. هذه الميزة غير مدعومة حالياً."
            )
        
        return VerifyCodeResponse(
            success=False,
            message=f"خطأ في التحقق: {str(e)}"
        )


@router.get("/me", response_model=BusinessInfo)
async def get_current_business(business_id: int):
    """
    Get current business info by ID.
    In production, this would use JWT tokens.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return BusinessInfo(
            id=business.id,
            phone=business.phone,
            name=business.name,
            city=business.city,
            is_active=business.is_active,
            telegram_id=business.telegram_id
        )
