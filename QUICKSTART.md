# 🚀 SyncVault AI - Quick Start Guide

## ⚡ Get Started in 2 Minutes

### Backend is Already Running! ✅

The backend server is running at: **http://localhost:8000**

Check API documentation: **http://localhost:8000/docs**

### Open the Frontend

**Option 1: Direct File (Easiest)**
```bash
# Open in your browser:
file:///home/mazyad/sync-vault/frontend.html
```

**Option 2: HTTP Server**
```bash
cd /home/mazyad/sync-vault
python3 -m http.server 5173

# Then open: http://localhost:5173/frontend.html
```

---

## 🧪 Test the System (5 Minutes)

### 1. Signup (30 seconds)

Open frontend → Fill signup form:
- **Phone:** +919876543210
- **Store Name:** My Test Store
- **Location:** Mumbai

Click "Signup" → Then switch to "Login"

### 2. Login with OTP (1 minute)

1. Enter phone: +919876543210
2. Click "Send OTP"
3. **Check backend terminal for OTP** (it will print something like: `OTP for +919876543210: 123456`)
4. Enter the OTP
5. Click "Verify & Login"

You're in! 🎉

### 3. Add Products (1 minute)

**Option A: Bulk Upload (Recommended)**

Use the sample CSV file:
```bash
curl -X POST http://localhost:8000/products/bulk-upload \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@/home/mazyad/sync-vault/sample_products.csv"
```

**Option B: Quick Add (Frontend)**

In the **Products** tab:
- Barcode: `1234567890123`
- Name: `Coca Cola 500ml`
- Price: `40`
- Category: `Beverages`
- Reorder Point: `20`
- Initial Quantity: `100`

Click "Add Product"

### 4. Test Barcode Scanning (1 minute)

1. Go to **Scan** tab
2. Enter barcode: `1234567890123` (or any barcode from sample CSV)
3. Click **"🛒 Sale (-1)"**
4. See success message ✅
5. Go to **Dashboard** tab
6. See quantity decreased!

### 5. Test Real-Time Updates (2 minutes)

**The Magic Moment:**

1. Open **2 browser tabs** with the frontend
2. Login in both tabs (same phone number)
3. In **Tab 1**: Go to Scan → Scan a barcode
4. In **Tab 2**: Watch dashboard → **It updates INSTANTLY** (no page reload!)

This is the WebSocket real-time update in action! 🚀

---

## 📊 What You Can Do Now

### View Inventory
```bash
GET http://localhost:8000/inventory
Authorization: Bearer YOUR_TOKEN
```

### Scan Barcode (Sale)
```bash
POST http://localhost:8000/inventory/scan
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "barcode": "8901030531248",
  "action": "sale",
  "quantity": 1
}
```

### Scan Barcode (Restock)
```bash
POST http://localhost:8000/inventory/scan
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "barcode": "8901030531248",
  "action": "restock",
  "quantity": 10
}
```

### Get Alerts
```bash
GET http://localhost:8000/alerts?acknowledged=false
Authorization: Bearer YOUR_TOKEN
```

### Run Forecasts
```bash
POST http://localhost:8000/forecasts/run
Authorization: Bearer YOUR_TOKEN
```

### Get Specific Forecast
```bash
GET http://localhost:8000/forecasts/1
Authorization: Bearer YOUR_TOKEN
```

---

## 🎯 Sample Products in CSV

The `sample_products.csv` includes 20 popular Indian products:

1. Coca Cola 500ml - ₹40
2. Pepsi 500ml - ₹40
3. Lays Chips 50g - ₹20
4. Kurkure Masala Munch - ₹10
5. Dairy Milk Chocolate - ₹30
6. Maggi Noodles - ₹12
7. Amul Milk 500ml - ₹25
8. Amul Butter 100g - ₹50
9. Nescafe Coffee - ₹150
10. ... and 10 more!

All with real Indian barcodes (EAN-13 format).

---

## 🔥 Key Features to Test

### ✅ Real-Time WebSocket Updates
- Open 2 tabs → Scan in one → Other updates instantly
- No page reload needed!

### ✅ AI Forecasting
- Add products → Make sales for 30 days → Run forecast
- See "Days until stockout" predictions

### ✅ Auto Alerts
- When quantity < reorder_point → Alert created automatically
- Check **Alerts** tab

### ✅ Bulk CSV Upload
- Upload sample_products.csv → All 20 products added at once

### ✅ Color-Coded Status
- 🟢 Green: Healthy stock
- 🟡 Yellow: Low stock
- 🔴 Red: Critical (below reorder point)

---

## 🐛 Troubleshooting

### Backend Not Running?
```bash
cd /home/mazyad/sync-vault/backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Can't See OTP?
Check the backend terminal output. OTP is printed like:
```
==================================================
📱 OTP for +919876543210: 123456
⏰ Expires at: 2025-12-11 09:05:00
==================================================
```

### WebSocket Not Connecting?
- Make sure backend is running
- Check browser console for errors
- Frontend URL should be: `file://` or `http://localhost:5173`

### Frontend Not Loading?
- Backend must be running first
- CORS is configured for `http://localhost:5173` and `file://`
- Try opening in a different browser

---

## 📝 API Token

After login, you'll get a JWT token. Save it for API calls.

**Get it from:**
1. Frontend: Check browser localStorage → `syncvault_token`
2. API: POST /auth/verify-otp → Response contains `access_token`

**Use it in all API calls:**
```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🚀 Next Steps

1. ✅ Test the system locally
2. Add more products (or use bulk CSV)
3. Make some sales (scan barcodes)
4. Check forecasts
5. **Deploy to production:**
   - Backend → Railway.app
   - Frontend → Vercel
   - Database → PostgreSQL on Railway

---

## 💡 Tips

- **Barcode Scanner:** If you have a physical barcode scanner, it works as a keyboard input
- **Multiple Stores:** Each store has isolated inventory (multi-tenancy built-in)
- **Forecasting:** Needs 30 days of transaction data for accurate predictions
- **Alerts:** Auto-created when inventory drops below reorder point

---

## 🎉 You're Ready!

**Everything is running:**
- ✅ Backend: http://localhost:8000
- ✅ API Docs: http://localhost:8000/docs
- ✅ Frontend: file:///home/mazyad/sync-vault/frontend.html
- ✅ Database: SQLite (syncvault.db)
- ✅ WebSocket: ws://localhost:8000/ws/{store_id}

**Start testing and watch the magic happen!** 🚀

For full documentation, see [README.md](file:///home/mazyad/sync-vault/README.md)
