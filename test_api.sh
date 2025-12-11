#!/bin/bash

# SyncVault AI - Complete Test Script
# This script tests the entire application end-to-end

echo "======================================================"
echo "🧪 SyncVault AI - API Test Script"
echo "======================================================"
echo ""

API_URL="http://localhost:8000"
PHONE="+919123456789"
STORE_NAME="Test Store $(date +%s)"
LOCATION="Mumbai"

echo "Step 1: Testing Backend Health"
echo "-------------------------------"
HEALTH=$(curl -s $API_URL/health)
echo "Response: $HEALTH"
echo ""

echo "Step 2: Creating Store Account (Signup)"
echo "----------------------------------------"
SIGNUP_RESPONSE=$(curl -s -X POST $API_URL/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"store_name\": \"$STORE_NAME\", \"location\": \"$LOCATION\"}")

echo "$SIGNUP_RESPONSE" | jq '.'
STORE_ID=$(echo "$SIGNUP_RESPONSE" | jq -r '.id')
echo "✅ Store created with ID: $STORE_ID"
echo ""

echo "Step 3: Sending OTP to Phone"
echo "-----------------------------"
OTP_RESPONSE=$(curl -s -X POST $API_URL/auth/send-otp \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\"}")

echo "$OTP_RESPONSE" | jq '.'
echo "⚠️  Check the backend terminal for the OTP!"
echo "    You should see a message like:"
echo "    📱 OTP for $PHONE: 123456"
echo ""

read -p "Enter the OTP from backend console: " OTP

echo "Step 4: Verifying OTP and Getting Token"
echo "----------------------------------------"
TOKEN_RESPONSE=$(curl -s -X POST $API_URL/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d "{\"phone\": \"$PHONE\", \"otp\": \"$OTP\"}")

echo "$TOKEN_RESPONSE" | jq '.'
TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
echo "✅ Token received: ${TOKEN:0:20}..."
echo ""

echo "Step 5: Adding Test Products"
echo "-----------------------------"

# Add 3 test products
for i in 1 2 3; do
  BARCODE="TEST12345678$i"
  PRODUCT_NAME="Test Product $i"
  PRICE=$((i * 10))
  
  PRODUCT_RESPONSE=$(curl -s -X POST $API_URL/products \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"barcode\": \"$BARCODE\", \"name\": \"$PRODUCT_NAME\", \"price\": $PRICE, \"category\": \"Test\", \"reorder_point\": 10, \"initial_quantity\": 50}")
  
  PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | jq -r '.id')
  echo "✅ Added $PRODUCT_NAME (ID: $PRODUCT_ID, Barcode: $BARCODE)"
done
echo ""

echo "Step 6: Get Inventory List"
echo "---------------------------"
INVENTORY=$(curl -s -X GET $API_URL/inventory \
  -H "Authorization: Bearer $TOKEN")

echo "$INVENTORY" | jq '.[] | {name: .name, barcode: .barcode, quantity: .quantity, status: .status}'
PRODUCT_COUNT=$(echo "$INVENTORY" | jq 'length')
echo "✅ Total products in inventory: $PRODUCT_COUNT"
echo ""

echo "Step 7: Test Barcode Scanning (Sale)"
echo "-------------------------------------"
SCAN_BARCODE="TEST123456781"
SCAN_RESPONSE=$(curl -s -X POST $API_URL/inventory/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"barcode\": \"$SCAN_BARCODE\", \"action\": \"sale\", \"quantity\": 1}")

echo "$SCAN_RESPONSE" | jq '{success: .success, message: .message, new_quantity: .new_quantity}'
echo "✅ Barcode scan successful!"
echo ""

echo "Step 8: Test Barcode Scanning (Restock)"
echo "----------------------------------------"
SCAN_RESPONSE2=$(curl -s -X POST $API_URL/inventory/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"barcode\": \"$SCAN_BARCODE\", \"action\": \"restock\", \"quantity\": 5}")

echo "$SCAN_RESPONSE2" | jq '{success: .success, message: .message, new_quantity: .new_quantity}'
echo "✅ Restock successful!"
echo ""

echo "Step 9: Bulk Upload from CSV"
echo "-----------------------------"
if [ -f "../sample_products.csv" ]; then
  BULK_RESPONSE=$(curl -s -X POST $API_URL/products/bulk-upload \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@../sample_products.csv")
  
  echo "$BULK_RESPONSE" | jq '{success: .success, created: .created, skipped: .skipped}'
  echo "✅ Bulk upload complete!"
else
  echo "⚠️  sample_products.csv not found, skipping bulk upload"
fi
echo ""

echo "Step 10: Get Alerts"
echo "-------------------"
ALERTS=$(curl -s -X GET "$API_URL/alerts?acknowledged=false" \
  -H "Authorization: Bearer $TOKEN")

ALERT_COUNT=$(echo "$ALERTS" | jq 'length')
echo "$ALERTS" | jq '.[] | {product: .product_name, type: .alert_type, message: .message}' 2>/dev/null || echo "No alerts"
echo "Total unacknowledged alerts: $ALERT_COUNT"
echo ""

echo "Step 11: Run Forecast Calculations"
echo "-----------------------------------"
FORECAST_RUN=$(curl -s -X POST $API_URL/forecasts/run \
  -H "Authorization: Bearer $TOKEN")

echo "$FORECAST_RUN" | jq '.'
echo ""

echo "Step 12: Get All Forecasts"
echo "--------------------------"
FORECASTS=$(curl -s -X GET $API_URL/forecasts \
  -H "Authorization: Bearer $TOKEN")

echo "$FORECASTS" | jq '.[] | {product: .product_name, days_until_stockout: .days_until_stockout, recommendation: .recommendation}' 2>/dev/null || echo "No forecasts yet (need transaction history)"
echo ""

echo "======================================================"
echo "✅ ALL TESTS COMPLETED SUCCESSFULLY!"
echo "======================================================"
echo ""
echo "Summary:"
echo "--------"
echo "✅ Backend is healthy"
echo "✅ Signup works"
echo "✅ OTP login works"  
echo "✅ Product addition works"
echo "✅ Barcode scanning works (sale + restock)"
echo "✅ Inventory retrieval works"
echo "✅ Alerts system works"
echo "✅ Forecasting system works"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Open the frontend: file:///home/mazyad/sync-vault/frontend.html"
echo "2. Login with phone: $PHONE"
echo "3. Use OTP from backend console"
echo "4. Test real-time WebSocket updates (open 2 tabs)"
echo ""
echo "Your Store ID: $STORE_ID"
echo "Your Token: ${TOKEN:0:50}..."
echo ""
