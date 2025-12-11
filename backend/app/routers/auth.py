from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from typing import Optional

from app.database import get_db, Store

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "720"))  # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate Limiting Storage (In-memory)
login_attempts = {}

# Pydantic Models
class SignupRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    store_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    location: Optional[str] = None

class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=1)

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    store_id: int
    store_name: str

class StoreResponse(BaseModel):
    id: int
    name: str
    phone: str
    location: Optional[str]
    api_key: str
    created_at: datetime

# Helper Functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_store(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
) -> Store:
    """Get current authenticated store"""
    store_id = payload.get("store_id")
    if not store_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
    
    return store

def check_rate_limit(phone: str):
    """Check if user is locked out"""
    if phone in login_attempts:
        attempts, lock_until = login_attempts[phone]
        if lock_until and datetime.utcnow() < lock_until:
             raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Try again in 15 minutes."
            )
        if lock_until and datetime.utcnow() > lock_until:
            # Reset lock
             login_attempts[phone] = [0, None]

def record_failed_attempt(phone: str):
    """Record failed login attempt"""
    if phone not in login_attempts:
        login_attempts[phone] = [1, None]
    else:
        attempts, lock_until = login_attempts[phone]
        login_attempts[phone] = [attempts + 1, lock_until]
        
        if login_attempts[phone][0] >= 5:
             login_attempts[phone][1] = datetime.utcnow() + timedelta(minutes=15)
             raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Try again in 15 minutes."
            )

def reset_attempts(phone: str):
    if phone in login_attempts:
        del login_attempts[phone]

# Routes
@router.post("/signup", response_model=StoreResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Create new store account with password"""
    # Check if phone already exists
    existing = db.query(Store).filter(Store.phone == request.phone).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered. Please login."
        )
    
    # Use phone as API key base for uniqueness + random
    import secrets
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Create store
    new_store = Store(
        name=request.store_name,
        phone=request.phone,
        location=request.location,
        password_hash=get_password_hash(request.password),
        api_key=api_key
    )
    
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    
    return new_store

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with phone and password"""
    check_rate_limit(request.phone)

    store = db.query(Store).filter(Store.phone == request.phone).first()
    
    if not store or not verify_password(request.password, store.password_hash):
        record_failed_attempt(request.phone)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password"
        )
    
    # Reset attempts on success
    reset_attempts(request.phone)
    
    # Create JWT token
    access_token = create_access_token({"store_id": store.id, "phone": store.phone})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        store_id=store.id,
        store_name=store.name
    )

@router.post("/logout")
async def logout():
    """Logout (Client should discard token)"""
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Change password for current user"""
    if not verify_password(request.old_password, current_store.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password"
        )
    
    current_store.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.get("/me", response_model=StoreResponse)
async def get_current_user(current_store: Store = Depends(get_current_store)):
    """Get current authenticated store details"""
    return current_store
