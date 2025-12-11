from app.database import Product, Store, Inventory, Transaction
from datetime import datetime, timedelta

def test_run_forecast(client, auth_token, db_session):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    store = db_session.query(Store).filter(Store.phone == "+919999999999").first()
    
    product = Product(
        store_id=store.id,
        barcode="55555",
        name="Forecast Item",
        price=20.0
    )
    db_session.add(product)
    db_session.flush()
    
    # Add inventory
    inv = Inventory(product_id=product.id, store_id=store.id, quantity=100)
    db_session.add(inv)
    
    # Add fake transactions
    for i in range(5):
        t = Transaction(
            product_id=product.id,
            store_id=store.id,
            quantity_change=5,
            transaction_type="out",
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        db_session.add(t)
    db_session.commit()
    
    # Run Forecast
    response = client.post("/forecasts/run", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "recalculated" in data
    
    # Optionally verify list of forecasts
    list_response = client.get("/forecasts/", headers=headers)
    assert list_response.status_code == 200
    forecasts = list_response.json()
    assert isinstance(forecasts, list)
    assert len(forecasts) >= 1
