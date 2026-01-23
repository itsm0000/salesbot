
import asyncio
import sys
import os

# Add the current directory to sys.path to make imports work
sys.path.append(os.getcwd())

from src.backend.database import init_db, async_session, Business, Product

async def seed_data():
    print("Initializing database...")
    await init_db()
    
    async with async_session() as session:
        # Check if business already exists
        from sqlalchemy import select
        result = await session.execute(select(Business).where(Business.phone == "+9647701234567"))
        existing_business = result.scalar_one_or_none()
        
        if existing_business:
            print("Test business already exists. ID:", existing_business.id)
            return existing_business.id
            
        print("Creating test business...")
        business = Business(
            phone="+9647701234567",
            name="Baghdad Lighting Solutions",
            city="Baghdad",
            business_type="Lighting & Electronics",
            telegram_id=123456789,
            session_string="dummy_session_string",
            is_active=False
        )
        session.add(business)
        await session.flush() # flush to get ID
        
        print(f"Created business with ID: {business.id}")
        
        # Add some products
        products = [
            Product(
                business_id=business.id,
                name="Smart LED Bulb RGB",
                name_ar="مصباح ذكي ملون",
                description="WiFi controlled smart bulb with 16M colors",
                price=15000,
                currency="IQD",
                in_stock=True
            ),
            Product(
                business_id=business.id,
                name="Crystal Chandelier 5-Arm",
                name_ar="ثريا كريستال 5 أذرع",
                description="Modern crystal chandelier for living rooms",
                price=120000,
                currency="IQD",
                in_stock=True
            )
        ]
        
        session.add_all(products)
        await session.commit()
        print("Added sample products.")
        return business.id

if __name__ == "__main__":
    # Windows SelectorEventLoop policy fix
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(seed_data())
