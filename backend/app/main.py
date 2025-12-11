from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.database import init_db, get_db, Store
from app.routers import auth, inventory, products, alerts, forecasts
from app.websocket_manager import manager
from app.middleware import LoggingMiddleware

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="SyncVault AI - Inventory Management API",
    description="Real-time inventory management system for retail stores",
    version="1.0.0"
)

# CORS configuration
# Strict CORS: Only allow specific origins in production
cors_origins_str = os.getenv("CORS_ORIGINS", "")
cors_origins = cors_origins_str.split(",") if cors_origins_str else ["http://localhost:5173", "http://localhost:3000"]

# Add 'null' to allow file:// origins (for local HTML files) - Development only
if os.getenv("ENVIRONMENT") == "development":
    cors_origins.append("null")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Custom Logging & Rate Limiting Middleware
app.add_middleware(LoggingMiddleware)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting SyncVault AI Backend...")
    init_db()
    print("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Shutting down SyncVault AI Backend...")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "SyncVault AI - Real-Time Inventory Management API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "syncvault-api"}

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{store_id}")
async def websocket_endpoint(websocket: WebSocket, store_id: int, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time inventory updates
    Clients connect with their store_id to receive live updates
    """
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        await websocket.close(code=4004, reason="Store not found")
        return
    
    # Connect client
    await manager.connect(websocket, store_id)
    
    # Send welcome message
    await manager.send_personal_message({
        "type": "connection_established",
        "message": f"Connected to SyncVault AI - Store: {store.name}",
        "store_id": store_id
    }, websocket)
    
    try:
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back (can be used for heartbeat/ping)
            await manager.send_personal_message({
                "type": "pong",
                "message": "Server alive"
            }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, store_id)
        print(f"Client disconnected from store {store_id}")

# Include routers
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(products.router)
app.include_router(alerts.router)
app.include_router(forecasts.router)

# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
