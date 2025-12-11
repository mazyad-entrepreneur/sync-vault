from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
import pandas as pd
import io

from app.database import get_db, Store, Product, Inventory
from app.routers.auth import get_current_store
from app.services.barcode_service import BarcodeService

router = APIRouter(prefix="/products", tags=["Products"])


# Pydantic Models
class ProductCreate(BaseModel):
    barcode: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0)
    category: Optional[str] = None
    reorder_point: int = Field(default=20, gt=0)
    initial_quantity: int = Field(default=0, ge=0)

    @validator('barcode', 'name', 'category')
    def strip_whitespace(cls, v):
        if v:
            return v.strip()
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = None
    reorder_point: Optional[int] = Field(None, gt=0)


class ProductResponse(BaseModel):
    id: int
    barcode: str
    name: str
    price: Decimal
    category: Optional[str]
    reorder_point: int
    current_quantity: int


class ProductListResponse(BaseModel):
    total: int
    products: List[ProductResponse]


class BulkUploadResponse(BaseModel):
    success: bool
    created: int
    skipped: int
    errors: List[str]


# Routes
@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Create new product"""
    # Validate barcode
    if not BarcodeService.validate_barcode(product.barcode):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid barcode format"
        )
    
    # Check if barcode already exists for this store
    if not BarcodeService.is_barcode_unique(product.barcode, current_store.id, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with barcode '{product.barcode}' already exists in your store"
        )
    
    # Create product
    new_product = Product(
        store_id=current_store.id,
        barcode=product.barcode,
        name=product.name,
        price=product.price,
        category=product.category,
        reorder_point=product.reorder_point
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Create inventory record
    new_inventory = Inventory(
        product_id=new_product.id,
        store_id=current_store.id,
        quantity=product.initial_quantity
    )
    db.add(new_inventory)
    db.commit()
    db.refresh(new_inventory)
    
    return ProductResponse(
        id=new_product.id,
        barcode=new_product.barcode,
        name=new_product.name,
        price=new_product.price,
        category=new_product.category,
        reorder_point=new_product.reorder_point,
        current_quantity=new_inventory.quantity
    )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = 0,
    limit: int = 100,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """List all products for store with pagination"""
    # Get total count
    total = db.query(Product).filter(Product.store_id == current_store.id).count()
    
    # Get products with inventory
    products = db.query(Product).filter(
        Product.store_id == current_store.id
    ).offset(skip).limit(limit).all()
    
    result = []
    for prod in products:
        inventory = db.query(Inventory).filter(Inventory.product_id == prod.id).first()
        result.append(ProductResponse(
            id=prod.id,
            barcode=prod.barcode,
            name=prod.name,
            price=prod.price,
            category=prod.category,
            reorder_point=prod.reorder_point,
            current_quantity=inventory.quantity if inventory else 0
        ))
    
    return ProductListResponse(total=total, products=result)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get single product by ID"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    
    return ProductResponse(
        id=product.id,
        barcode=product.barcode,
        name=product.name,
        price=product.price,
        category=product.category,
        reorder_point=product.reorder_point,
        current_quantity=inventory.quantity if inventory else 0
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    update: ProductUpdate,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Update product details"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Update fields
    if update.name is not None:
        product.name = update.name
    if update.price is not None:
        product.price = update.price
    if update.category is not None:
        product.category = update.category
    if update.reorder_point is not None:
        product.reorder_point = update.reorder_point
    
    db.commit()
    db.refresh(product)
    
    inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    
    return ProductResponse(
        id=product.id,
        barcode=product.barcode,
        name=product.name,
        price=product.price,
        category=product.category,
        reorder_point=product.reorder_point,
        current_quantity=inventory.quantity if inventory else 0
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Delete product"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    db.delete(product)
    db.commit()
    
    return {"success": True, "message": "Product deleted successfully"}


@router.post("/bulk-upload", response_model=BulkUploadResponse)
async def bulk_upload_products(
    file: UploadFile = File(...),
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """
    Bulk upload products from CSV file
    Expected columns: barcode, name, price, category, reorder_point, initial_quantity
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate required columns
        required_columns = ['barcode', 'name', 'price']
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required column: {col}"
                )
        
        # Optional columns with defaults
        if 'category' not in df.columns:
            df['category'] = None
        if 'reorder_point' not in df.columns:
            df['reorder_point'] = 20
        if 'initial_quantity' not in df.columns:
            df['initial_quantity'] = 0
        
        created = 0
        skipped = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Validate barcode
                barcode = str(row['barcode']).strip()
                
                if not BarcodeService.validate_barcode(barcode):
                    errors.append(f"Row {index + 2}: Invalid barcode format '{barcode}'")
                    skipped += 1
                    continue
                
                # Check if barcode already exists
                if not BarcodeService.is_barcode_unique(barcode, current_store.id, db):
                    errors.append(f"Row {index + 2}: Barcode '{barcode}' already exists")
                    skipped += 1
                    continue
                
                # Create product
                new_product = Product(
                    store_id=current_store.id,
                    barcode=barcode,
                    name=str(row['name']).strip(),
                    price=Decimal(str(row['price'])),
                    category=str(row['category']).strip() if pd.notna(row['category']) else None,
                    reorder_point=int(row['reorder_point'])
                )
                db.add(new_product)
                db.flush()  # Get product ID
                
                # Create inventory
                new_inventory = Inventory(
                    product_id=new_product.id,
                    store_id=current_store.id,
                    quantity=int(row['initial_quantity'])
                )
                db.add(new_inventory)
                
                created += 1
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                skipped += 1
        
        db.commit()
        
        return BulkUploadResponse(
            success=True,
            created=created,
            skipped=skipped,
            errors=errors[:10]  # Return max 10 errors
        )
        
    except pd.errors.ParserError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV file format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
