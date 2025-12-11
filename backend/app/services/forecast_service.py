from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import Transaction, Product, Inventory, Forecast
from decimal import Decimal
import statistics


class ForecastService:
    """Service for AI-powered inventory forecasting"""
    
    @staticmethod
    def calculate_forecast(product_id: int, store_id: int, db: Session) -> Optional[Dict]:
        """
        Calculate forecast for a product based on 30-day transaction history
        
        Args:
            product_id: Product ID
            store_id: Store ID
            db: Database session
        
        Returns:
            Dictionary with forecast data or None
        """
        # Get product and inventory
        product = db.query(Product).filter(Product.id == product_id).first()
        inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        
        if not product or not inventory:
            return None
        
        # Get last 30 days of transactions (sales only)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        transactions = db.query(Transaction).filter(
            Transaction.product_id == product_id,
            Transaction.store_id == store_id,
            Transaction.transaction_type == 'out',  # Sales only
            Transaction.created_at >= thirty_days_ago
        ).all()
        
        if not transactions:
            # No sales history - can't forecast
            return {
                "product_id": product_id,
                "days_until_stockout": None,
                "confidence": 0.0,
                "avg_daily_sales": 0.0,
                "recommendation": "No sales history available"
            }
        
        # Group transactions by date and sum daily sales
        daily_sales = {}
        for txn in transactions:
            date_key = txn.created_at.date()
            if date_key not in daily_sales:
                daily_sales[date_key] = 0
            daily_sales[date_key] += abs(txn.quantity_change)
        
        # Calculate average daily sales
        sales_values = list(daily_sales.values())
        avg_daily_sales = sum(sales_values) / len(sales_values) if sales_values else 0
        
        # Calculate confidence based on sales variability
        if len(sales_values) > 1:
            std_dev = statistics.stdev(sales_values)
            # Lower variability = higher confidence
            confidence = max(0.0, min(1.0, 1 - (std_dev / (avg_daily_sales + 1))))
        else:
            confidence = 0.5  # Medium confidence with limited data
        
        # Predict days until stockout
        current_qty = inventory.quantity
        if avg_daily_sales > 0:
            days_until_stockout = int(current_qty / avg_daily_sales)
        else:
            days_until_stockout = None
        
        # Generate recommendation
        recommendation = ForecastService._generate_recommendation(
            days_until_stockout, 
            current_qty, 
            product.reorder_point
        )
        
        return {
            "product_id": product_id,
            "days_until_stockout": days_until_stockout,
            "confidence": round(float(confidence), 2),
            "avg_daily_sales": round(float(avg_daily_sales), 2),
            "recommendation": recommendation
        }
    
    @staticmethod
    def _generate_recommendation(days_until_stockout: Optional[int], current_qty: int, reorder_point: int) -> str:
        """Generate reorder recommendation based on forecast"""
        if days_until_stockout is None:
            return "Monitor sales - insufficient data"
        
        if current_qty < reorder_point:
            return "🔴 URGENT: Already below reorder point!"
        
        if days_until_stockout <= 3:
            return "🔴 URGENT REORDER: Will stockout in 3 days or less"
        elif days_until_stockout <= 7:
            return "🟡 Schedule reorder this week"
        elif days_until_stockout <= 14:
            return "🟢 Reorder in next 2 weeks"
        else:
            return "✅ Stock healthy"
    
    @staticmethod
    def save_forecast(forecast_data: Dict, store_id: int, db: Session) -> Forecast:
        """Save forecast to database"""
        existing = db.query(Forecast).filter(
            Forecast.product_id == forecast_data["product_id"],
            Forecast.store_id == store_id
        ).first()
        
        if existing:
            # Update existing forecast
            existing.days_until_stockout = forecast_data["days_until_stockout"]
            existing.confidence = Decimal(str(forecast_data["confidence"]))
            existing.avg_daily_sales = Decimal(str(forecast_data["avg_daily_sales"]))
            existing.recommendation = forecast_data["recommendation"]
            existing.last_recalculated = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new forecast
            new_forecast = Forecast(
                product_id=forecast_data["product_id"],
                store_id=store_id,
                days_until_stockout=forecast_data["days_until_stockout"],
                confidence=Decimal(str(forecast_data["confidence"])),
                avg_daily_sales=Decimal(str(forecast_data["avg_daily_sales"])),
                recommendation=forecast_data["recommendation"]
            )
            db.add(new_forecast)
            db.commit()
            db.refresh(new_forecast)
            return new_forecast
    
    @staticmethod
    def recalculate_all_forecasts(store_id: int, db: Session) -> int:
        """Recalculate forecasts for all products in store"""
        products = db.query(Product).filter(Product.store_id == store_id).all()
        count = 0
        
        for product in products:
            forecast_data = ForecastService.calculate_forecast(product.id, store_id, db)
            if forecast_data:
                ForecastService.save_forecast(forecast_data, store_id, db)
                count += 1
        
        return count
