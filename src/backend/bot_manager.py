"""
Multi-Session Sales Bot Manager
Manages Telethon clients for multiple business owners
"""
import os
import sys
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Add parent directory for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.brain import Brain

# Telegram API credentials
API_ID = os.getenv("TELEGRAM_API_ID", "30619302")
API_HASH = os.getenv("TELEGRAM_API_HASH", "a501dc4dd3e7e2288cdc3dc18ff9e3ce")


@dataclass
class BusinessBot:
    """Represents a running bot instance for a business owner"""
    business_id: int
    telegram_id: int
    client: TelegramClient
    brain: Brain
    is_running: bool = False
    config: Dict[str, Any] = field(default_factory=dict)


class BotManager:
    """
    Manages multiple Telethon clients, one per business.
    Each business owner's bot runs on their own Telegram account.
    """
    
    def __init__(self):
        self.bots: Dict[int, BusinessBot] = {}  # business_id -> BusinessBot
        self._message_queue = asyncio.Queue(maxsize=100)
        self._workers: list[asyncio.Task] = []
        self._data_dir = Path(__file__).parent.parent.parent / "data"
        self._config_dir = Path(__file__).parent.parent.parent / "config"
    
    def _create_brain_for_business(self, business_config: Dict[str, Any]) -> Brain:
        """Create a Brain instance with business-specific config"""
        products_path = str(self._data_dir / "products.csv")
        config_path = str(self._config_dir / "business_config.json")
        
        brain = Brain(
            products_path=products_path,
            business_config_path=config_path,
        )
        
        # Override with business-specific settings if provided
        if business_config:
            if business_config.get('business_name'):
                brain.business_name = business_config['business_name']
            if business_config.get('business_city'):
                brain.business_city = business_config['business_city']
        
        return brain
    
    async def start_for_business(
        self,
        business_id: int,
        session_string: str,
        business_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Start a bot instance for a specific business.
        
        Args:
            business_id: Database ID of the business
            session_string: Telethon StringSession data
            business_config: Optional business settings
            
        Returns:
            True if started successfully
        """
        if business_id in self.bots and self.bots[business_id].is_running:
            print(f"⚠️ Bot for business {business_id} already running")
            return True
        
        try:
            # Create client from session string
            client = TelegramClient(
                StringSession(session_string),
                API_ID,
                API_HASH
            )
            
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"❌ Session for business {business_id} is not authorized")
                return False
            
            me = await client.get_me()
            
            # Create Brain for this business
            brain = self._create_brain_for_business(business_config or {})
            
            # Create bot instance
            bot = BusinessBot(
                business_id=business_id,
                telegram_id=me.id,
                client=client,
                brain=brain,
                is_running=True,
                config=business_config or {}
            )
            
            # Load products from database
            await self._load_business_products(business_id, brain)
            
            # Set up message handler
            self._setup_handler(bot)
            
            # Store bot
            self.bots[business_id] = bot
            
            print(f"✅ Started bot for business {business_id} ({me.first_name})")
            return True
            
        except Exception as e:
            print(f"❌ Error starting bot for business {business_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _load_business_products(self, business_id: int, brain: Brain):
        """Load products from DB into Brain's knowledge"""
        from .database import async_session, Product as DBProduct
        from sqlalchemy import select
        from core.knowledge import Product as KnowledgeProduct
        
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(DBProduct).where(DBProduct.business_id == business_id)
                )
                db_products = result.scalars().all()
                
                brain.knowledge.products.clear()
                
                for p in db_products:
                    k_product = KnowledgeProduct(
                        id=str(p.id),
                        name=p.name,
                        description=p.description or "",
                        price=int(p.price) if p.price else 0,
                        stock=p.quantity or (100 if p.in_stock else 0),
                        category="General", # TODO: Add category to DB model fully
                        attributes=[]
                    )
                    brain.knowledge.products[k_product.id] = k_product
                    
                print(f"📚 Loaded {len(db_products)} products for business {business_id}")
                
        except Exception as e:
            print(f"⚠️ Error loading products for business {business_id}: {e}")
    
    def _setup_handler(self, bot: BusinessBot):
        """Set up message handler for a business's bot"""
        
        @bot.client.on(events.NewMessage(incoming=True))
        async def handle_message(event):
            # Only handle private messages (DMs from customers)
            if not event.is_private:
                return
            
            sender = await event.get_sender()
            sender_name = sender.first_name if sender else "Unknown"
            sender_id = sender.id if sender else 0
            
            # FEEDBACK LOOP PREVENTION: Skip messages from other business accounts
            other_business_telegram_ids = [
                b.telegram_id for b in self.bots.values() 
                if b.telegram_id != bot.telegram_id
            ]
            if sender_id in other_business_telegram_ids:
                print(f"⚠️ Skipping message from another business bot")
                return
            
            # Skip non-text messages for now (could be extended for product photos)
            if not event.text:
                return
            
            print(f"💬 Business {bot.business_id}: Message from {sender_name}: {event.text[:50]}...")
            
            # Queue the message for processing
            await self._message_queue.put({
                'bot': bot,
                'event': event,
                'sender_id': sender_id,
                'sender_name': sender_name,
                'chat_id': event.chat_id,
                'message': event.text
            })
    
    async def _message_worker(self, worker_id: int):
        """Worker that processes customer messages"""
        print(f"[Worker {worker_id}] Started")
        
        while True:
            try:
                job = await self._message_queue.get()
                
                bot = job['bot']
                event = job['event']
                sender_id = job['sender_id']
                sender_name = job['sender_name']
                message = job['message']
                
                print(f"[Worker {worker_id}] Processing for business {bot.business_id}")
                
                try:
                    # Process through Brain
                    result = await bot.brain.process_message(
                        message=message,
                        customer_id=str(sender_id),
                        platform="telegram"
                    )
                    
                    # Send response
                    await bot.client.send_message(
                        job['chat_id'],
                        result.response_text
                    )
                    
                    print(f"[Worker {worker_id}] Responded to {sender_name} (confidence: {result.confidence_score})")
                    
                except Exception as e:
                    print(f"[Worker {worker_id}] Error: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Send fallback message
                    try:
                        await bot.client.send_message(
                            job['chat_id'],
                            "عذراً حجي، صار خطأ تقني. دقيقة وأرد عليك..."
                        )
                    except:
                        pass
                
                finally:
                    self._message_queue.task_done()
                    
            except asyncio.CancelledError:
                break
    
    async def start_workers(self, num_workers: int = 3):
        """Start message processing workers"""
        for i in range(num_workers):
            task = asyncio.create_task(self._message_worker(i + 1))
            self._workers.append(task)
        print(f"🚀 Started {num_workers} message workers")
    
    async def stop_for_business(self, business_id: int):
        """Stop a bot for a specific business"""
        if business_id not in self.bots:
            return
        
        bot = self.bots[business_id]
        bot.is_running = False
        await bot.client.disconnect()
        del self.bots[business_id]
        
        print(f"🛑 Stopped bot for business {business_id}")
    
    async def update_config(self, business_id: int, config: Dict[str, Any]):
        """Update the config for a business's bot"""
        if business_id in self.bots:
            bot = self.bots[business_id]
            bot.config.update(config)
            
            # Update Brain settings
            if config.get('business_name'):
                bot.brain.business_name = config['business_name']
            if config.get('business_city'):
                bot.brain.business_city = config['business_city']
            
            print(f"📝 Updated config for business {business_id}")
    
    async def stop_all(self):
        """Stop all bots and workers"""
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        # Disconnect all bots
        for business_id in list(self.bots.keys()):
            await self.stop_for_business(business_id)
        
        print("🛑 All bots stopped")
    
    async def start_all_from_db(self, db_session):
        """
        Start bots for all active businesses from database.
        Called on server startup.
        """
        from .database import Business
        from sqlalchemy import select
        
        # Get all active businesses with sessions
        result = await db_session.execute(
            select(Business).where(
                Business.is_active == True,
                Business.session_string != None
            )
        )
        businesses = result.scalars().all()
        
        print(f"🔄 Starting bots for {len(businesses)} businesses...")
        
        for business in businesses:
            config = {
                'business_name': business.name,
                'business_city': business.city,
            }
            
            await self.start_for_business(
                business.id,
                business.session_string,
                config
            )
        
        # Start workers
        await self.start_workers(3)
    
    def get_status(self, business_id: int) -> Dict[str, Any]:
        """Get status of a business's bot"""
        if business_id not in self.bots:
            return {"running": False, "connected": False}
        
        bot = self.bots[business_id]
        return {
            "running": bot.is_running,
            "connected": bot.client.is_connected(),
            "telegram_id": bot.telegram_id,
        }


# Global instance
bot_manager = BotManager()
