from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from app.logging_config import setup_logging

logger = setup_logging()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Log Request
        logger.info(json.dumps({
            "event": "request_received",
            "request_id": request_id, 
            "method": request.method, 
            "path": request.url.path,
            "client": request.client.host
        }))
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log Response
            logger.info(json.dumps({
                "event": "response_sent",
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(process_time * 1000, 2)
            }))
            
            response.headers["X-Request-ID"] = request_id
            return response
            
        except Exception as e:
            logger.error(json.dumps({
                "event": "request_failed",
                "request_id": request_id,
                "error": str(e)
            }))
            raise
    
import json
