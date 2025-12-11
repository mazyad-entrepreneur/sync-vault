from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db, Store, Alert, Product
from app.routers.auth import get_current_store

router = APIRouter(prefix="/alerts", tags=["Alerts"])


# Pydantic Models
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    message: str
    acknowledged: bool
    created_at: datetime
    product_id: int
    product_name: str
    product_barcode: str


class AcknowledgeRequest(BaseModel):
    alert_id: int


# Routes
@router.get("/", response_model=List[AlertResponse])
async def get_all_alerts(
    acknowledged: Optional[bool] = None,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all alerts for current store"""
    query = db.query(Alert, Product).join(
        Product, Alert.product_id == Product.id
    ).filter(Alert.store_id == current_store.id)
    
    # Filter by acknowledged status if provided
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    
    # Order by created_at descending (newest first)
    alerts = query.order_by(Alert.created_at.desc()).all()
    
    result = []
    for alert, product in alerts:
        result.append(AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            message=alert.message,
            acknowledged=alert.acknowledged,
            created_at=alert.created_at,
            product_id=product.id,
            product_name=product.name,
            product_barcode=product.barcode
        ))
    
    return result


@router.post("/acknowledge")
async def acknowledge_alert(
    request: AcknowledgeRequest,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Mark alert as acknowledged"""
    alert = db.query(Alert).filter(
        Alert.id == request.alert_id,
        Alert.store_id == current_store.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    alert.acknowledged = True
    db.commit()
    
    return {"success": True, "message": "Alert acknowledged"}


@router.get("/low-stock", response_model=List[AlertResponse])
async def get_low_stock_alerts(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all low stock alerts"""
    alerts = db.query(Alert, Product).join(
        Product, Alert.product_id == Product.id
    ).filter(
        Alert.store_id == current_store.id,
        Alert.alert_type == "low_stock",
        Alert.acknowledged == False
    ).order_by(Alert.created_at.desc()).all()
    
    result = []
    for alert, product in alerts:
        result.append(AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            message=alert.message,
            acknowledged=alert.acknowledged,
            created_at=alert.created_at,
            product_id=product.id,
            product_name=product.name,
            product_barcode=product.barcode
        ))
    
    return result


@router.get("/expiry", response_model=List[AlertResponse])
async def get_expiry_alerts(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all expiry alerts (future feature)"""
    alerts = db.query(Alert, Product).join(
        Product, Alert.product_id == Product.id
    ).filter(
        Alert.store_id == current_store.id,
        Alert.alert_type == "expiry",
        Alert.acknowledged == False
    ).order_by(Alert.created_at.desc()).all()
    
    result = []
    for alert, product in alerts:
        result.append(AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            message=alert.message,
            acknowledged=alert.acknowledged,
            created_at=alert.created_at,
            product_id=product.id,
            product_name=product.name,
            product_barcode=product.barcode
        ))
    
    return result


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.store_id == current_store.id
    ).first()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {"success": True, "message": "Alert deleted"}
