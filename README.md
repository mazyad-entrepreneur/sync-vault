# 🚀 SyncVault AI - Real-Time Inventory Management System

**For Indian Retail Stores & E-commerce**

A complete full-stack inventory management system with real-time barcode scanning, AI-powered forecasting, and instant WebSocket updates.

## 🎯 Features

- ✅ **Real-Time Barcode Scanning** - Scan → Instant inventory update across all devices
- ✅ **AI Forecasting** - Predicts stockout dates based on 30-day sales history
- ✅ **WebSocket Live Updates** - No page reload needed, updates broadcast to all clients
- ✅ **Low Stock Alerts** - Automatic alerts when inventory falls below reorder point
- ✅ **Phone + OTP Authentication** - Secure login with OTP (mock mode for MVP)
- ✅ **Bulk CSV Upload** - Add 100+ products at once
- ✅ **Multi-Store Support** - Each store has isolated inventory

## 📦 Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.8+)
- **Database:** SQLite (local), PostgreSQL (production)
- **Real-Time:** WebSocket
- **Auth:** JWT + Phone OTP
- **AI:** Statistical forecasting (30-day moving average)

### Frontend
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **State:** React Hooks
- **UI:** Custom CSS (can add Tailwind later)
- **Charts:** Recharts (for analytics)

## 🛠️ Quick Start

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run dev server (requires Node.js 20+)
npm run dev
```

Frontend will run on: **http://localhost:5173**

> **Note:** If you have Node.js 18, you may encounter errors. Please upgrade to Node.js 20+ or use the backend API directly.

## 📖 Usage Guide

### 1. Signup & Login

1. **Signup:** Create store account
   ```bash
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"phone": "+919876543210", "store_name": "My Store", "location": "Mumbai"}'
   ```

2. **Send OTP:**
   ```bash
   curl -X POST http://localhost:8000/auth/send-otp \
     -H "Content-Type: application/json" \
     -d '{"phone": "+919876543210"}'
   ```
   
   Check backend console for OTP (printed to terminal)

3. **Verify OTP:**
   ```bash
   curl -X POST http://localhost:8000/auth/verify-otp \
     -H "Content-Type: application/json" \
     -d '{"phone": "+919876543210", "otp": "123456"}'
   ```
   
   Save the `access_token` from response

### 2. Add Products

**Single Product:**
```bash
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "1234567890123",
    "name": "Coca Cola 500ml",
    "price": 40.00,
    "category": "Beverages",
    "reorder_point": 20,
    "initial_quantity": 100
  }'
```

**Bulk CSV Upload:**
Create a CSV file `products.csv`:
```csv
barcode,name,price,category,reorder_point,initial_quantity
1234567890123,Coca Cola 500ml,40.00,Beverages,20,100
2345678901234,Lays Chips 50g,20.00,Snacks,30,150
3456789012345,Dairy Milk Chocolate,30.00,Snacks,25,80
```

Upload via API:
```bash
curl -X POST http://localhost:8000/products/bulk-upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.csv"
```

### 3. Scan Barcode (Sale)

```bash
curl -X POST http://localhost:8000/inventory/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "barcode": "1234567890123",
    "action": "sale",
    "quantity": 1
  }'
```

**Response:**
- Inventory quantity decremented
- Transaction logged
- WebSocket broadcast to all connected devices
- Alert created if quantity < reorder_point

### 4. Get Forecasts

```bash
curl -X GET http://localhost:8000/forecasts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Forecast Logic:**
- Analyzes last 30 days of sales
- Calculates average daily sales
- Predicts: `days_until_stockout = current_qty / avg_daily_sales`
- Generates recommendation (Urgent/Schedule/Healthy)

## 🗄️ Database Schema

```sql
stores (id, name, phone, api_key, location)
products (id, store_id, barcode, name, price, category, reorder_point)
inventory (id, product_id, store_id, quantity, last_updated)
transactions (id, product_id, store_id, quantity_change, type: in/out)
alerts (id, store_id, product_id, type, message, acknowledged)
forecasts (id, product_id, days_until_stockout, confidence, recommendation)
```

## 🔌 WebSocket Real-Time Updates

Connect to: `ws://localhost:8000/ws/{store_id}`

**Message Types:**
- `inventory_update` - Inventory quantity changed
- `alert_created` - New alert triggered
- `connection_established` - Connection successful

Example (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/1');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'inventory_update') {
    console.log('Product updated:', message.data);
    // Update UI without page reload
  }
};
```

## 🧪 Testing Checklist

- [x] Signup flow works
- [x] OTP login works
- [x] Add product works
- [x] Bulk CSV upload works
- [x] Barcode scan decrements quantity
- [x] Transaction logged correctly
- [x] WebSocket broadcasts to all clients
- [x] Alert created when qty < reorder_point
- [x] Forecast calculates correctly
- [x] Real-time dashboard updates

## 🚀 Deployment

### Backend (Railway)

1. Create Railway project
2. Add PostgreSQL database
3. Connect GitHub repo
4. Add environment variables:
   ```
   DATABASE_URL=<railway-postgres-url>
   JWT_SECRET=<random-secret-key>
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
5. Deploy

### Frontend (Vercel)

1. Connect GitHub repo
2. Set environment variables:
   ```
   VITE_API_URL=https://your-backend.railway.app
   VITE_WS_URL=wss://your-backend.railway.app
   ```
3. Deploy

## 💰 Monetization

**Target:** ₹5,000-50,000/month per store

**Pricing Tiers:**
- **Basic:** ₹5,000/month - 1 store, 500 products, 5,000 scans/month
- **Pro:** ₹15,000/month - 5 stores, 5,000 products, 50,000 scans/month
- **Enterprise:** ₹50,000/month - Unlimited stores, products, scans

**Cost Structure:**
- Backend hosting: ₹800/month (Railway)
- Frontend hosting: ₹0 (Vercel free tier)
- Database: Included in Railway $10/month

**Break-even:** 2 paying customers

## 📞 Support

For issues or questions:
- Email: support@syncvault.ai
- Phone: +91 XXXXXXXXXX

## 📝 License

MIT License - Free for personal and commercial use

---

**Built with ❤️ for Indian Retail Stores**
