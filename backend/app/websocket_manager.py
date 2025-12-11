from fastapi import WebSocket
from typing import Dict, List
import json


class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store connections per store_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, store_id: int):
        """Accept WebSocket connection and add to store's connection pool"""
        await websocket.accept()
        
        if store_id not in self.active_connections:
            self.active_connections[store_id] = []
        
        self.active_connections[store_id].append(websocket)
        print(f"✅ WebSocket connected for store {store_id}. Total connections: {len(self.active_connections[store_id])}")
    
    def disconnect(self, websocket: WebSocket, store_id: int):
        """Remove WebSocket connection from store's pool"""
        if store_id in self.active_connections:
            if websocket in self.active_connections[store_id]:
                self.active_connections[store_id].remove(websocket)
                print(f"❌ WebSocket disconnected for store {store_id}. Remaining: {len(self.active_connections[store_id])}")
            
            # Clean up empty lists
            if not self.active_connections[store_id]:
                del self.active_connections[store_id]
    
    async def broadcast(self, store_id: int, message: dict):
        """Send message to all connected clients for a specific store"""
        if store_id not in self.active_connections:
            return
        
        disconnected = []
        message_json = json.dumps(message)
        
        for connection in self.active_connections[store_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"⚠️  Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, store_id)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"⚠️  Error sending personal message: {e}")


# Global WebSocket manager instance
manager = WebSocketManager()
