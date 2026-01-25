"""
Operator API Routes
Multi-bot management endpoints for the operator dashboard
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio
import json
import hashlib

from ..database import async_session, Operator, Business, BotMemory, Message, Conversation
from .auth import get_current_business  # We'll extend this for operators

router = APIRouter(prefix="/api/operator", tags=["operator"])


# ============ Pydantic Models ============

class OperatorLogin(BaseModel):
    phone: str
    password: str


class OperatorCreate(BaseModel):
    phone: str
    name: str
    password: str


class BotCreate(BaseModel):
    phone: str
    name: str
    city: Optional[str] = None
    business_type: Optional[str] = None


class BotMemoryUpdate(BaseModel):
    persona_name: Optional[str] = None
    persona_prompt: Optional[str] = None
    tone: Optional[str] = None
    permanent_memory: Optional[dict] = None
    max_discount_percent: Optional[int] = None
    shipping_baghdad: Optional[int] = None
    shipping_other: Optional[int] = None


class BotStatusResponse(BaseModel):
    id: int
    name: str
    city: Optional[str]
    is_active: bool
    is_connected: bool
    telegram_id: Optional[int]
    messages_today: int
    last_message_at: Optional[datetime]


# ============ Helper Functions ============

def hash_password(password: str) -> str:
    """Simple password hashing (use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_operator_by_phone(phone: str) -> Optional[Operator]:
    """Get operator by phone number"""
    async with async_session() as session:
        result = await session.execute(
            select(Operator).where(Operator.phone == phone)
        )
        return result.scalar_one_or_none()


# ============ Authentication Routes ============

@router.post("/login")
async def operator_login(data: OperatorLogin):
    """Operator login with phone and password"""
    operator = await get_operator_by_phone(data.phone)
    
    if not operator:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if operator.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not operator.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    
    return {
        "success": True,
        "operator_id": operator.id,
        "name": operator.name,
        "phone": operator.phone
    }


@router.post("/register")
async def operator_register(data: OperatorCreate):
    """Register a new operator (first-time setup)"""
    existing = await get_operator_by_phone(data.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    async with async_session() as session:
        operator = Operator(
            phone=data.phone,
            name=data.name,
            password_hash=hash_password(data.password),
            is_active=True
        )
        session.add(operator)
        await session.commit()
        await session.refresh(operator)
        
        return {
            "success": True,
            "operator_id": operator.id,
            "message": "Operator account created"
        }


# ============ Bot Management Routes ============

@router.get("/bots")
async def list_bots(operator_id: int = Query(...)):
    """List all bots for an operator with their status"""
    from ..bot_manager import bot_manager
    
    async with async_session() as session:
        result = await session.execute(
            select(Business)
            .options(selectinload(Business.conversations))
            .where(Business.operator_id == operator_id)
            .order_by(Business.created_at.desc())
        )
        businesses = result.scalars().all()
        
        bots = []
        for biz in businesses:
            # Get bot status from manager
            status = bot_manager.get_status(biz.id)
            
            # Count today's messages
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            messages_today = 0
            last_message_at = None
            
            for conv in biz.conversations:
                if conv.last_message_at and conv.last_message_at >= today:
                    messages_today += conv.messages_count
                if not last_message_at or (conv.last_message_at and conv.last_message_at > last_message_at):
                    last_message_at = conv.last_message_at
            
            bots.append({
                "id": biz.id,
                "name": biz.name,
                "city": biz.city,
                "business_type": biz.business_type,
                "is_active": biz.is_active,
                "is_connected": status.get("connected", False),
                "telegram_id": biz.telegram_id,
                "messages_today": messages_today,
                "last_message_at": last_message_at.isoformat() if last_message_at else None,
                "products_count": len(biz.products) if hasattr(biz, 'products') else 0
            })
        
        return {"bots": bots, "total": len(bots)}


@router.get("/bots/{bot_id}")
async def get_bot(bot_id: int):
    """Get detailed info for a single bot"""
    from ..bot_manager import bot_manager
    
    async with async_session() as session:
        result = await session.execute(
            select(Business)
            .options(
                selectinload(Business.products),
                selectinload(Business.bot_memory),
                selectinload(Business.conversations).selectinload(Conversation.messages)
            )
            .where(Business.id == bot_id)
        )
        biz = result.scalar_one_or_none()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        status = bot_manager.get_status(bot_id)
        
        # Get recent messages
        recent_messages = []
        for conv in biz.conversations:
            for msg in sorted(conv.messages, key=lambda m: m.timestamp, reverse=True)[:20]:
                recent_messages.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "customer_name": conv.customer_name
                })
        
        return {
            "id": biz.id,
            "name": biz.name,
            "city": biz.city,
            "business_type": biz.business_type,
            "phone": biz.phone,
            "telegram_id": biz.telegram_id,
            "is_active": biz.is_active,
            "is_connected": status.get("connected", False),
            "target_audience": biz.target_audience,
            "products": [
                {"id": p.id, "name": p.name, "price": p.price, "in_stock": p.in_stock}
                for p in biz.products
            ],
            "memory": {
                "persona_name": biz.bot_memory.persona_name if biz.bot_memory else None,
                "persona_prompt": biz.bot_memory.persona_prompt if biz.bot_memory else None,
                "tone": biz.bot_memory.tone if biz.bot_memory else "friendly",
                "max_discount_percent": biz.bot_memory.max_discount_percent if biz.bot_memory else 10,
            } if biz.bot_memory else None,
            "recent_messages": recent_messages[:20]
        }


@router.post("/bots/{bot_id}/start")
async def start_bot(bot_id: int):
    """Start a bot instance"""
    from ..bot_manager import bot_manager
    
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == bot_id)
        )
        biz = result.scalar_one_or_none()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        if not biz.session_string:
            raise HTTPException(status_code=400, detail="No Telegram session configured")
        
        # Start the bot
        config = {
            "business_name": biz.name,
            "business_city": biz.city,
        }
        
        success = await bot_manager.start_for_business(
            biz.id,
            biz.session_string,
            config
        )
        
        if success:
            biz.is_active = True
            await session.commit()
            return {"success": True, "message": f"Bot {biz.name} started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start bot")


@router.post("/bots/{bot_id}/stop")
async def stop_bot(bot_id: int):
    """Stop a bot instance"""
    from ..bot_manager import bot_manager
    
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == bot_id)
        )
        biz = result.scalar_one_or_none()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        await bot_manager.stop_for_business(bot_id)
        
        biz.is_active = False
        await session.commit()
        
        return {"success": True, "message": f"Bot {biz.name} stopped"}


@router.put("/bots/{bot_id}/memory")
async def update_bot_memory(bot_id: int, data: BotMemoryUpdate):
    """Update bot's persistent memory and persona"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).options(selectinload(Business.bot_memory))
            .where(Business.id == bot_id)
        )
        biz = result.scalar_one_or_none()
        
        if not biz:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        # Create or update BotMemory
        if not biz.bot_memory:
            memory = BotMemory(business_id=bot_id)
            session.add(memory)
        else:
            memory = biz.bot_memory
        
        # Update fields
        if data.persona_name is not None:
            memory.persona_name = data.persona_name
        if data.persona_prompt is not None:
            memory.persona_prompt = data.persona_prompt
        if data.tone is not None:
            memory.tone = data.tone
        if data.permanent_memory is not None:
            memory.permanent_memory = data.permanent_memory
        if data.max_discount_percent is not None:
            memory.max_discount_percent = data.max_discount_percent
        if data.shipping_baghdad is not None:
            memory.shipping_baghdad = data.shipping_baghdad
        if data.shipping_other is not None:
            memory.shipping_other = data.shipping_other
        
        await session.commit()
        
        return {"success": True, "message": "Bot memory updated"}


# ============ Real-time Message Stream ============

@router.get("/bots/{bot_id}/messages/stream")
async def message_stream(bot_id: int):
    """Server-Sent Events stream for real-time messages"""
    
    async def event_generator():
        last_check = datetime.utcnow()
        
        while True:
            async with async_session() as session:
                # Get new messages since last check
                result = await session.execute(
                    select(Message)
                    .join(Conversation)
                    .where(
                        Conversation.business_id == bot_id,
                        Message.timestamp > last_check
                    )
                    .order_by(Message.timestamp)
                )
                messages = result.scalars().all()
                
                for msg in messages:
                    conv = await session.get(Conversation, msg.conversation_id)
                    data = {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "customer_name": conv.customer_name if conv else "Unknown"
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                if messages:
                    last_check = messages[-1].timestamp
            
            await asyncio.sleep(2)  # Poll every 2 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/bots")
async def create_bot(data: BotCreate, operator_id: int = Query(...)):
    """Create a new bot instance (Telegram auth handled separately)"""
    async with async_session() as session:
        # Check if phone already exists
        result = await session.execute(
            select(Business).where(Business.phone == data.phone)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone already registered")
        
        # Create business
        business = Business(
            operator_id=operator_id,
            phone=data.phone,
            name=data.name,
            city=data.city,
            business_type=data.business_type,
            is_active=False
        )
        session.add(business)
        await session.commit()
        await session.refresh(business)
        
        # Create default bot memory
        memory = BotMemory(
            business_id=business.id,
            tone="iraqi",
            max_discount_percent=10
        )
        session.add(memory)
        await session.commit()
        
        return {
            "success": True,
            "bot_id": business.id,
            "message": f"Bot '{data.name}' created. Configure Telegram session to start."
        }
