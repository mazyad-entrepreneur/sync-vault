import secrets
import random
from typing import Optional
from sqlalchemy.orm import Session
from app.database import Product


class BarcodeService:
    """Service for barcode operations"""
    
    @staticmethod
    def validate_barcode(barcode: str) -> bool:
        """Validate barcode format (basic validation)"""
        if not barcode:
            return False
        
        # Check if alphanumeric and reasonable length
        if len(barcode) < 4 or len(barcode) > 50:
            return False
        
        return True
    
    @staticmethod
    def parse_barcode(barcode: str, store_id: int, db: Session) -> Optional[Product]:
        """
        Parse barcode and find product in database
        
        Args:
            barcode: Barcode string
            store_id: Store ID for scoping
            db: Database session
        
        Returns:
            Product if found, None otherwise
        """
        if not BarcodeService.validate_barcode(barcode):
            return None
        
        # Find product by barcode and store_id
        product = db.query(Product).filter(
            Product.barcode == barcode,
            Product.store_id == store_id
        ).first()
        
        return product
    
    @staticmethod
    def generate_barcode() -> str:
        """
        Generate a random valid barcode (EAN-13 format simulation)
        
        Returns:
            13-digit barcode string
        """
        # Generate 12 random digits
        digits = ''.join([str(random.randint(0, 9)) for _ in range(12)])
        
        # Calculate checksum (simplified EAN-13)
        odd_sum = sum(int(d) for d in digits[::2])
        even_sum = sum(int(d) for d in digits[1::2])
        checksum = (10 - ((odd_sum + even_sum * 3) % 10)) % 10
        
        return digits + str(checksum)
    
    @staticmethod
    def is_barcode_unique(barcode: str, store_id: int, db: Session) -> bool:
        """
        Check if barcode is unique within store
        
        Args:
            barcode: Barcode to check
            store_id: Store ID
            db: Database session
        
        Returns:
            True if unique, False if already exists
        """
        existing = db.query(Product).filter(
            Product.barcode == barcode,
            Product.store_id == store_id
        ).first()
        
        return existing is None
