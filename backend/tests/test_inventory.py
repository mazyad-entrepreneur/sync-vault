from app.database import Product, Store, Inventory

def test_add_product_and_update_inventory(client, auth_token, db_session):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # helper to get store id from token? simplified: querying DB for user created by auth_token
    store = db_session.query(Store).filter(Store.phone == "+919999999999").first()
    
    # Create Product manually
    product = Product(
        store_id=store.id,
        barcode="123456789",
        name="Test Product",
        price=10.0,
        category="Test"
    )
    db_session.add(product)
    
    # Create initial inventory for it
    inventory = Inventory(
        product_id=None, # will be set after flush? No, need product id.
        store_id=store.id,
        quantity=0 
    )
    # Actually, SQLAlchemy usually needs flushing.
    db_session.flush() # get product id
    inventory.product_id = product.id
    db_session.add(inventory)
    db_session.commit()
    
    # Update Inventory via Scan (Restock)
    response = client.post("/inventory/scan", json={
        "barcode": "123456789",
        "action": "restock",
        "quantity": 10
    }, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["new_quantity"] == 10

def test_scan_item_view(client, auth_token, db_session):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Ensure product exists (conftest scope is function, so we need to re-create or split tests)
    # Since scope is function, data is rolled back. We need to create data again.
    store = db_session.query(Store).filter(Store.phone == "+919999999999").first()
    product = Product(
        store_id=store.id,
        barcode="987654321",
        name="View Product",
        price=10.0
    )
    db_session.add(product)
    db_session.flush()
    inventory = Inventory(product_id=product.id, store_id=store.id, quantity=5)
    db_session.add(inventory)
    db_session.commit()
    
    # Test List View
    response = client.get("/inventory/", headers=headers)
    assert response.status_code == 200
    items = response.json()
    found = next((i for i in items if i["barcode"] == "987654321"), None)
    assert found is not None
    assert found["name"] == "View Product"
    assert found["quantity"] == 5
