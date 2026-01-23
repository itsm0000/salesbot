"""
Database models and setup for Muntazir Sales Bot
"""
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# Database URL (default to SQLite)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite+aiosqlite:///{Path(__file__).parent.parent.parent / 'data' / 'muntazir.db'}"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Business(Base):
    """Business owner / sales bot user"""
    __tablename__ = "businesses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    business_type: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "electronics", "clothing"
    
    # Telegram session
    telegram_id: Mapped[Optional[int]] = mapped_column(Integer)
    session_string: Mapped[Optional[str]] = mapped_column(Text)
    
    # Bot settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_personality: Mapped[Optional[str]] = mapped_column(Text)  # Custom personality prompt
    auto_reply: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Config JSON for flexible settings
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products: Mapped[list["Product"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="business", cascade="all, delete-orphan")


class Product(Base):
    """Products/services offered by a business"""
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200))  # Arabic name
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Optional[float]] = mapped_column()
    currency: Mapped[str] = mapped_column(String(10), default="IQD")
    
    # Stock/availability
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Media
    photo_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    business: Mapped["Business"] = relationship(back_populates="products")


class Conversation(Base):
    """Conversation history with customers"""
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    
    customer_telegram_id: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Conversation state
    last_message_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Sales tracking
    interested_products: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    sale_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    business: Mapped["Business"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual messages in a conversation"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    
    role: Mapped[str] = mapped_column(String(20))  # "customer" or "bot"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI metadata
    confidence: Mapped[Optional[float]] = mapped_column()
    flags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables created")


async def get_session() -> AsyncSession:
    """Get a database session"""
    async with async_session() as session:
        yield session
