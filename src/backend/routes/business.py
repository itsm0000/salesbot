"""
Business management routes - Config, Products, Bot Control
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session, Business, Product
from ..bot_manager import bot_manager

router = APIRouter()


# ============ Models ============

class BusinessConfig(BaseModel):
    name: str
    city: Optional[str] = None
    business_type: Optional[str] = None
    ai_personality: Optional[str] = None
    target_audience: Optional[str] = "عام"
    auto_reply: bool = True


# ... (skipping to update_config) ...

@router.put("/config/{business_id}", response_model=BusinessConfig)
async def update_config(business_id: int, config: BusinessConfig):
    """Update business configuration"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business.name = config.name
        business.city = config.city
        business.business_type = config.business_type
        business.ai_personality = config.ai_personality
        business.target_audience = config.target_audience
        business.auto_reply = config.auto_reply
        
        await session.commit()
        
        # Update running bot if exists
        await bot_manager.update_config(business_id, {
            'business_name': config.name,
            'business_city': config.city,
            'target_audience': config.target_audience,
        })


class ProductCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "IQD"
    in_stock: bool = True
    quantity: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    name_ar: Optional[str]
    description: Optional[str]
    price: Optional[float]
    currency: str
    in_stock: bool
    quantity: Optional[int]


class BotStatus(BaseModel):
    running: bool
    connected: bool
    telegram_id: Optional[int] = None


class StartBotResponse(BaseModel):
    success: bool
    message: str


# ============ Config Routes ============

@router.get("/config/{business_id}", response_model=BusinessConfig)
async def get_config(business_id: int):
    """Get business configuration"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        return BusinessConfig(
            name=business.name,
            city=business.city,
            business_type=business.business_type,
            ai_personality=business.ai_personality,
            auto_reply=business.auto_reply
        )


@router.put("/config/{business_id}", response_model=BusinessConfig)
async def update_config(business_id: int, config: BusinessConfig):
    """Update business configuration"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business.name = config.name
        business.city = config.city
        business.business_type = config.business_type
        business.ai_personality = config.ai_personality
        business.auto_reply = config.auto_reply
        
        await session.commit()
        
        # Update running bot if exists
        await bot_manager.update_config(business_id, {
            'business_name': config.name,
            'business_city': config.city,
        })
        
        return config


# ============ Product Routes ============

@router.get("/products/{business_id}", response_model=List[ProductResponse])
async def get_products(business_id: int):
    """Get all products for a business"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.business_id == business_id)
        )
        products = result.scalars().all()
        
        return [ProductResponse(
            id=p.id,
            name=p.name,
            name_ar=p.name_ar,
            description=p.description,
            price=p.price,
            currency=p.currency,
            in_stock=p.in_stock,
            quantity=p.quantity
        ) for p in products]


@router.post("/products/{business_id}", response_model=ProductResponse)
async def add_product(business_id: int, product: ProductCreate):
    """Add a new product"""
    async with async_session() as session:
        # Verify business exists
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Business not found")
        
        new_product = Product(
            business_id=business_id,
            name=product.name,
            name_ar=product.name_ar,
            description=product.description,
            price=product.price,
            currency=product.currency,
            in_stock=product.in_stock,
            quantity=product.quantity
        )
        session.add(new_product)
        await session.commit()
        await session.refresh(new_product)
        
        return ProductResponse(
            id=new_product.id,
            name=new_product.name,
            name_ar=new_product.name_ar,
            description=new_product.description,
            price=new_product.price,
            currency=new_product.currency,
            in_stock=new_product.in_stock,
            quantity=new_product.quantity
        )


@router.delete("/products/{business_id}/{product_id}")
async def delete_product(business_id: int, product_id: int):
    """Delete a product"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(
                Product.id == product_id,
                Product.business_id == business_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        await session.delete(product)
        await session.commit()
        
        return {"success": True, "message": "Product deleted"}


# ============ Bot Control Routes ============

@router.get("/status/{business_id}", response_model=BotStatus)
async def get_bot_status(business_id: int):
    """Get bot status for a business"""
    status = bot_manager.get_status(business_id)
    return BotStatus(**status)


@router.post("/start/{business_id}", response_model=StartBotResponse)
async def start_bot(business_id: int):
    """Start the sales bot for a business"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        if not business.session_string:
            raise HTTPException(status_code=400, detail="No Telegram session. Please login first.")
        
        # Start the bot
        success = await bot_manager.start_for_business(
            business_id=business.id,
            session_string=business.session_string,
            business_config={
                'business_name': business.name,
                'business_city': business.city,
            }
        )
        
        if success:
            business.is_active = True
            await session.commit()
            return StartBotResponse(success=True, message="تم تشغيل البوت بنجاح! 🚀")
        else:
            return StartBotResponse(success=False, message="فشل تشغيل البوت. تحقق من الجلسة.")


@router.post("/stop/{business_id}", response_model=StartBotResponse)
async def stop_bot(business_id: int):
    """Stop the sales bot for a business"""
    async with async_session() as session:
        result = await session.execute(
            select(Business).where(Business.id == business_id)
        )
        business = result.scalar_one_or_none()
        
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")
        
        await bot_manager.stop_for_business(business_id)
        
        business.is_active = False
        await session.commit()
        
        return StartBotResponse(success=True, message="تم إيقاف البوت 🛑")
