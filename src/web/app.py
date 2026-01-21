"""
FastAPI Web Application
منتظر - واجهة الويب
"""

import os
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from ..core.brain import Brain
from ..core.personality import PersonalityConfig


# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
STATIC_DIR = Path(__file__).parent / "static"


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    customer_id: str = "default_customer"
    platform: str = "manual"


class ChatResponse(BaseModel):
    response: str
    confidence: float
    actions: list
    flags: dict
    processing_time_ms: int


class ProductUploadRequest(BaseModel):
    csv_content: str


class ConfigUpdateRequest(BaseModel):
    config: dict


# Initialize FastAPI app
app = FastAPI(
    title="Muntazir - Iraqi Sales AI",
    description="منتظر - وكيل مبيعات عراقي ذكي",
    version="0.1.0",
)

# Global brain instance (initialized on startup)
brain: Optional[Brain] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the Brain on startup"""
    global brain
    
    products_path = str(DATA_DIR / "products.csv")
    config_path = str(CONFIG_DIR / "business_config.json")
    
    try:
        brain = Brain(
            products_path=products_path,
            business_config_path=config_path,
        )
        print("✅ Brain initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Brain: {e}")
        raise


# Mount static files
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the main testing interface"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Muntazir - Interface Loading...</h1>")


@app.get("/styles.css")
async def serve_styles():
    """Serve CSS file"""
    css_path = STATIC_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return ""


# API Endpoints
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        result = await brain.process_message(
            message=request.message,
            customer_id=request.customer_id,
            platform=request.platform,
        )
        
        return ChatResponse(
            response=result.response_text,
            confidence=result.confidence_score,
            actions=result.suggested_actions,
            flags=result.flags,
            processing_time_ms=result.processing_time_ms,
        )
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products")
async def get_products():
    """Get all products"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    products = brain.knowledge.get_all_products()
    return {
        "products": [p.to_dict() for p in products],
        "total": len(products),
    }


@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get a specific product by ID"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    product = brain.knowledge.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product.to_dict()


@app.get("/api/products/search/{query}")
async def search_products(query: str):
    """Search products by query"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    products = brain.knowledge.search_products(query=query)
    return {
        "products": [p.to_dict() for p in products],
        "total": len(products),
    }


@app.get("/api/config")
async def get_config():
    """Get current business configuration"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    return brain.business_config


@app.put("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """Update business configuration"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    try:
        # Update in memory
        brain.business_config.update(request.config)
        
        # Persist to file
        config_path = CONFIG_DIR / "business_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(brain.business_config, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversation/{customer_id}")
async def clear_conversation(customer_id: str):
    """Clear conversation history for a customer"""
    global brain
    
    if not brain:
        raise HTTPException(status_code=500, detail="Brain not initialized")
    
    brain.clear_conversation(customer_id)
    return {"status": "success", "message": f"Conversation cleared for {customer_id}"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "brain_initialized": brain is not None,
        "products_loaded": len(brain.knowledge.products) if brain else 0,
    }
