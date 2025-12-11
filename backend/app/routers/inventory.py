from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.database import get_db, Store, Product, Inventory, Transaction, Alert
from app.routers.auth import get_current_store
from app.services.barcode_service import BarcodeService
from app.websocket_manager import manager

router = APIRouter(prefix="/inventory", tags=["Inventory"])


# Pydantic Models
class ScanRequest(BaseModel):
    barcode: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(sale|restock)$")
    quantity: int = Field(default=1, gt=0)

    @validator('barcode')
    def strip_whitespace(cls, v):
        return v.strip()


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(..., ge=0)


class InventoryItem(BaseModel):
    id: int
    product_id: int
    barcode: str
    name: str
    category: Optional[str]
    price: Decimal
    quantity: int
    reorder_point: int
    status: str  # healthy, low, critical
    last_updated: datetime


class ScanResponse(BaseModel):
    success: bool
    message: str
    product: InventoryItem
    new_quantity: int
    transaction_id: int


# Helper Functions
def get_inventory_status(quantity: int, reorder_point: int) -> str:
    """Determine inventory status based on quantity and reorder point"""
    if quantity >= reorder_point * 1.5:
        return "healthy"
    elif quantity < reorder_point:
        return "critical"
    else:
        return "low"


def create_low_stock_alert(product_id: int, store_id: int, quantity: int, db: Session):
    """Create low stock alert if needed"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if quantity < product.reorder_point:
        # Check if alert already exists
        existing_alert = db.query(Alert).filter(
            Alert.product_id == product_id,
            Alert.store_id == store_id,
            Alert.alert_type == "low_stock",
            Alert.acknowledged == False
        ).first()
        
        if not existing_alert:
            new_alert = Alert(
                store_id=store_id,
                product_id=product_id,
                alert_type="low_stock",
                message=f"Low stock alert: {product.name} has only {quantity} units left (reorder point: {product.reorder_point})"
            )
            db.add(new_alert)
            db.commit()
            return new_alert
    
    return None


# Routes
@router.get("/", response_model=List[InventoryItem])
async def get_inventory(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all inventory items for current store"""
    # Join inventory with products
    items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(
        Inventory.store_id == current_store.id
    ).all()
    
    result = []
    for inv, prod in items:
        status = get_inventory_status(inv.quantity, prod.reorder_point)
        result.append(InventoryItem(
            id=inv.id,
            product_id=prod.id,
            barcode=prod.barcode,
            name=prod.name,
            category=prod.category,
            price=prod.price,
            quantity=inv.quantity,
            reorder_point=prod.reorder_point,
            status=status,
            last_updated=inv.last_updated
        ))
    
    return result


@router.post("/scan", response_model=ScanResponse)
async def scan_barcode(
    request: ScanRequest,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """
    Scan barcode and update inventory (CORE FEATURE)
    - Sale: Decrements quantity
    - Restock: Increments quantity
    - Broadcasts update via WebSocket
    - Creates alert if low stock
    """
    # Find product by barcode
    product = BarcodeService.parse_barcode(request.barcode, current_store.id, db)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with barcode '{request.barcode}' not found in your store"
        )
    
    # Get inventory
    inventory = db.query(Inventory).filter(
        Inventory.product_id == product.id,
        Inventory.store_id == current_store.id
    ).first()
    
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory record not found"
        )
    
    # Calculate new quantity
    if request.action == "sale":
        if inventory.quantity < request.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock. Available: {inventory.quantity}, Requested: {request.quantity}"
            )
        new_quantity = inventory.quantity - request.quantity
        quantity_change = -request.quantity
        transaction_type = "out"
    else:  # restock
        new_quantity = inventory.quantity + request.quantity
        quantity_change = request.quantity
        transaction_type = "in"
    
    # Update inventory
    inventory.quantity = new_quantity
    inventory.last_updated = datetime.utcnow()
    
    # Create transaction record
    transaction = Transaction(
        product_id=product.id,
        store_id=current_store.id,
        quantity_change=quantity_change,
        transaction_type=transaction_type
    )
    db.add(transaction)
    db.commit()
    db.refresh(inventory)
    db.refresh(transaction)
    
    # Check and create alert if low stock
    alert = create_low_stock_alert(product.id, current_store.id, new_quantity, db)
    
    # Broadcast update via WebSocket
    status = get_inventory_status(new_quantity, product.reorder_point)
    update_message = {
        "type": "inventory_update",
        "data": {
            "product_id": product.id,
            "barcode": product.barcode,
            "name": product.name,
            "quantity": new_quantity,
            "status": status,
            "action": request.action,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    await manager.broadcast(current_store.id, update_message)
    
    # If alert was created, broadcast it too
    if alert:
        alert_message = {
            "type": "alert_created",
            "data": {
                "alert_id": alert.id,
                "product_name": product.name,
                "message": alert.message,
                "alert_type": alert.alert_type
            }
        }
        await manager.broadcast(current_store.id, alert_message)
    
    # Prepare response
    inventory_item = InventoryItem(
        id=inventory.id,
        product_id=product.id,
        barcode=product.barcode,
        name=product.name,
        category=product.category,
        price=product.price,
        quantity=new_quantity,
        reorder_point=product.reorder_point,
        status=status,
        last_updated=inventory.last_updated
    )
    
    return ScanResponse(
        success=True,
        message=f"{'Sale' if request.action == 'sale' else 'Restock'} successful: {product.name}",
        product=inventory_item,
        new_quantity=new_quantity,
        transaction_id=transaction.id
    )


@router.put("/{product_id}")
async def update_quantity(
    product_id: int,
    request: UpdateQuantityRequest,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Manual inventory quantity update"""
    # Get product and inventory
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    inventory = db.query(Inventory).filter(
        Inventory.product_id == product_id,
        Inventory.store_id == current_store.id
    ).first()
    
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory not found")
    
    # Calculate difference
    old_quantity = inventory.quantity
    quantity_change = request.quantity - old_quantity
    
    # Update inventory
    inventory.quantity = request.quantity
    inventory.last_updated = datetime.utcnow()
    
    # Create transaction
    transaction = Transaction(
        product_id=product_id,
        store_id=current_store.id,
        quantity_change=abs(quantity_change),
        transaction_type="in" if quantity_change > 0 else "out"
    )
    db.add(transaction)
    db.commit()
    db.refresh(inventory)
    
    # Check for low stock alert
    create_low_stock_alert(product_id, current_store.id, request.quantity, db)
    
    # Broadcast update
    status = get_inventory_status(request.quantity, product.reorder_point)
    await manager.broadcast(current_store.id, {
        "type": "inventory_update",
        "data": {
            "product_id": product_id,
            "quantity": request.quantity,
            "status": status
        }
    })
    
    return {
        "success": True,
        "message": "Inventory updated successfully",
        "old_quantity": old_quantity,
        "new_quantity": request.quantity
    }


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Delete product and its inventory"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Delete product (cascade will delete inventory, transactions, alerts, forecasts)
    db.delete(product)
    db.commit()
    
    return {"success": True, "message": "Product deleted successfully"}


@router.get("/low-stock", response_model=List[InventoryItem])
async def get_low_stock(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all products with low stock (below reorder point)"""
    items = db.query(Inventory, Product).join(
        Product, Inventory.product_id == Product.id
    ).filter(
        Inventory.store_id == current_store.id,
        Inventory.quantity < Product.reorder_point
    ).all()
    
    result = []
    for inv, prod in items:
        status = get_inventory_status(inv.quantity, prod.reorder_point)
        result.append(InventoryItem(
            id=inv.id,
            product_id=prod.id,
            barcode=prod.barcode,
            name=prod.name,
            category=prod.category,
            price=prod.price,
            quantity=inv.quantity,
            reorder_point=prod.reorder_point,
            status=status,
            last_updated=inv.last_updated
        ))
    
    return result
