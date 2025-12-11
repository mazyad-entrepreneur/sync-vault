from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from app.database import get_db, Store, Forecast, Product
from app.routers.auth import get_current_store
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


# Pydantic Models
class ForecastResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_barcode: str
    days_until_stockout: Optional[int]
    confidence: Optional[Decimal]
    avg_daily_sales: Optional[Decimal]
    recommendation: Optional[str]
    last_recalculated: datetime


class RunForecastResponse(BaseModel):
    success: bool
    recalculated: int
    message: str


# Routes
@router.get("/{product_id}", response_model=ForecastResponse)
async def get_product_forecast(
    product_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get forecast for specific product"""
    # Get product
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Get or calculate forecast
    forecast = db.query(Forecast).filter(
        Forecast.product_id == product_id,
        Forecast.store_id == current_store.id
    ).first()
    
    if not forecast:
        # Calculate new forecast
        forecast_data = ForecastService.calculate_forecast(product_id, current_store.id, db)
        if forecast_data:
            forecast = ForecastService.save_forecast(forecast_data, current_store.id, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unable to calculate forecast - insufficient data"
            )
    
    return ForecastResponse(
        id=forecast.id,
        product_id=product.id,
        product_name=product.name,
        product_barcode=product.barcode,
        days_until_stockout=forecast.days_until_stockout,
        confidence=forecast.confidence,
        avg_daily_sales=forecast.avg_daily_sales,
        recommendation=forecast.recommendation,
        last_recalculated=forecast.last_recalculated
    )


@router.get("/", response_model=List[ForecastResponse])
async def get_all_forecasts(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Get all forecasts for store"""
    forecasts = db.query(Forecast, Product).join(
        Product, Forecast.product_id == Product.id
    ).filter(
        Forecast.store_id == current_store.id
    ).order_by(Forecast.days_until_stockout.asc()).all()
    
    result = []
    for forecast, product in forecasts:
        result.append(ForecastResponse(
            id=forecast.id,
            product_id=product.id,
            product_name=product.name,
            product_barcode=product.barcode,
            days_until_stockout=forecast.days_until_stockout,
            confidence=forecast.confidence,
            avg_daily_sales=forecast.avg_daily_sales,
            recommendation=forecast.recommendation,
            last_recalculated=forecast.last_recalculated
        ))
    
    return result


@router.post("/run", response_model=RunForecastResponse)
async def run_forecast_calculation(
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """
    Recalculate forecasts for all products in store
    This can be scheduled to run daily via cron job
    """
    count = ForecastService.recalculate_all_forecasts(current_store.id, db)
    
    return RunForecastResponse(
        success=True,
        recalculated=count,
        message=f"Successfully recalculated {count} forecasts"
    )


@router.post("/{product_id}/recalculate", response_model=ForecastResponse)
async def recalculate_product_forecast(
    product_id: int,
    current_store: Store = Depends(get_current_store),
    db: Session = Depends(get_db)
):
    """Recalculate forecast for specific product"""
    # Get product
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.store_id == current_store.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Calculate forecast
    forecast_data = ForecastService.calculate_forecast(product_id, current_store.id, db)
    
    if not forecast_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to calculate forecast - insufficient transaction data"
        )
    
    # Save forecast
    forecast = ForecastService.save_forecast(forecast_data, current_store.id, db)
    
    return ForecastResponse(
        id=forecast.id,
        product_id=product.id,
        product_name=product.name,
        product_barcode=product.barcode,
        days_until_stockout=forecast.days_until_stockout,
        confidence=forecast.confidence,
        avg_daily_sales=forecast.avg_daily_sales,
        recommendation=forecast.recommendation,
        last_recalculated=forecast.last_recalculated
    )
