# 🍔 Burger Bills - Setup Complete! 

## ✅ System Ready to Use

Your fully automated QR code-based restaurant ordering system is now live!

### 🚀 Access Points

| Role | URL | Username | Password |
|------|-----|----------|----------|
| **Customer** | http://localhost:8000 | - | - |
| **Staff Dashboard** | http://localhost:8000/dashboard/ | admin | admin123 |
| **Admin Panel** | http://localhost:8000/admin/ | admin | admin123 |
| **Orders Management** | http://localhost:8000/orders/ | admin | admin123 |
| **Menu Management** | http://localhost:8000/menu-management/ | admin | admin123 |
| **Reports** | http://localhost:8000/reports/ | admin | admin123 |

---

## 📱 How to Use - Customer Experience

### Step 1: Scan Table QR Code
Each table has a unique QR code that customers can scan with their phone camera or QR code scanner.

**Sample QR Codes are auto-generated for:**
- Table 1 through Table 10
- Location: Admin Panel → Tables

### Step 2: Access Menu
After scanning, customer is taken to the menu for their specific table number.

**Menu Features:**
- 4 Categories: Burgers 🍔, Drinks 🥤, Sides 🍟, Desserts 🍰
- 11 Sample Items with descriptions and prices
- Professional images and ratings
- Vegetarian 🌱 and Spicy 🌶️ tags

### Step 3: Add Items to Cart
Click "Add" button on any item:
- Select quantity
- Add special requests (no onions, extra cheese, etc.)
- Item added to cart

### Step 4: Review Cart
Click "View Cart" to:
- See all items with quantities
- Adjust quantities
- Remove items
- Add special instructions for entire order
- See total amount

### Step 5: Submit Order
Click "Submit Order" to:
- Send order to kitchen
- Get order number and receipt
- See real-time order status

### Step 6: Track Order Status
Real-time tracking shows:
- ✅ Confirmed
- 🔥 Preparing
- ⏱️ Ready
- 📝 Complete

### Step 7: View Receipt
Professional receipt with:
- Order number
- Items and quantities
- Special requests
- Total amount
- Printable format

---

## 👨‍💼 How to Use - Staff Operations

### Dashboard (http://localhost:8000/dashboard/)
**Real-time monitoring with:**
- 📊 4 Key metrics (Pending orders, Preparing, Completed today, Revenue)
- 📋 Active orders list
- Quick status update buttons
- Auto-refreshes every 10 seconds

### Orders Management (http://localhost:8000/orders/)
**Comprehensive order management:**
- Filter by status (All, Pending, Confirmed, Preparing, Ready, Completed)
- View order details
- 📱 Table number for each order
- Total amounts
- Timestamp tracking

### Menu Management (http://localhost:8000/menu-management/)
**Quick overview of:**
- All categories with item counts
- Availability status
- Prices
- Direct edit links
- Quick actions for categories and tables

### Reports & Analytics (http://localhost:8000/reports/)
**Business insights:**
- 💰 Daily revenue
- 📈 Orders completed today
- 🔥 Top 5 selling items
- 📊 Performance metrics

### Full Admin Panel (http://localhost:8000/admin/)
**Complete management:**
- Add/edit Categories
- Add/edit Menu Items (with image uploads)
- Manage Tables (QR codes auto-generate)
- View/edit Orders
- User management
- Advanced filtering and searching

---

## 🗂️ Sample Data Included

### Categories (4)
| Icon | Category | Items |
|------|----------|-------|
| 🍔 | Burgers | 4 items |
| 🥤 | Drinks | 3 items |
| 🍟 | Sides | 3 items |
| 🍰 | Desserts | 2 items |

### Sample Burgers
1. **Classic Burger** - $12.99 ⭐ 4.5
2. **Cheese Burger** - $14.99 ⭐ 4.7
3. **Spicy Burger** - $15.99 🌶️ ⭐ 4.4
4. **Veggie Burger** - $13.99 🌱 ⭐ 4.2

### Sample Drinks
1. **Coca Cola** - $3.99 ⭐ 4.5
2. **Fresh Orange Juice** - $5.99 🌱 ⭐ 4.6
3. **Iced Coffee** - $4.99 ⭐ 4.4

### Tables
10 tables created (Table 1-10) with auto-generated QR codes

---

## 🎨 UI Features

### Customer Interface
✨ **Modern & Professional Design**
- Gradient navigation bar
- Responsive card layout
- Smooth animations and transitions
- Mobile-optimized (works on phones/tablets)
- Sticky category sidebar for easy navigation
- Real-time cart updates
- Toast notifications for feedback

### Staff Interface
📊 **Dashboard & Management**
- Color-coded status indicators
- Live updating metrics
- Quick action buttons
- Professional tables
- Filter options
- Real-time order tracking

---

## 🔧 Technical Details

### Database
- **Type**: SQLite3 (perfect for small to medium restaurants)
- **Location**: `db.sqlite3`
- **Auto-migrations**: Applied and tested

### Models
```
Category → MenuItem
Table → Order → OrderItem
         ↓
    MenuItem (reference)
```

### Authentication
- Django built-in authentication
- Staff-only views (login required)
- Secure CSRF protection

### Features
- QR code auto-generation for tables
- Real-time order status updates
- Special requests for each item
- Order number generation (ORD-YYYYMMDD-XXXX)
- Timestamps for all operations

---

## 🎯 Testing the System

### As a Customer
1. Open: http://localhost:8000/table/1/menu/
   - Table 1 menu appears
2. Click on a burger "Add" button
3. Select quantity 2
4. Add special request "No onions"
5. Click "Submit"
6. See order confirmation
7. Check real-time status updates

### As Staff
1. Go to: http://localhost:8000/dashboard/
2. See pending order
3. Click "Start Preparing"
4. Order moves to "Preparing" status
5. When ready, click "Ready"
6. When completed, click "Complete"

### Admin Panel
1. Go to: http://localhost:8000/admin/
2. Login: admin / admin123
3. Browse all models
4. Add new menu items
5. Create new tables (QR codes auto-generate)

---

## 📱 QR Codes

### How QR Codes Work
1. Each table has a unique QR code
2. QR code encodes: `https://burgerbills.local/table/{table_number}/menu/`
3. When scanned, customer's phone opens the menu for that specific table
4. System automatically knows which table the customer is at

### Printing QR Codes
1. Go to Admin Panel → Tables
2. Click each table
3. Download QR code image
4. Print on durable material (laminated)
5. Place on each table

### Sample Test QR Codes
Test links (no QR needed, for development):
- Table 1: http://localhost:8000/table/1/menu/
- Table 2: http://localhost:8000/table/2/menu/
- Table 3: http://localhost:8000/table/3/menu/
- (Continue for all 10 tables)

---

## 🔐 Security & Admin

### Login Credentials
```
Username: admin
Password: admin123
```

### What Admin Can Do
- ✅ Add/edit/delete all menu items
- ✅ Manage categories
- ✅ Create tables and generate QR codes
- ✅ View all orders and update status
- ✅ Create new staff users
- ✅ View reports and analytics

### Creating New Staff Users
1. Admin Panel → Users → Add User
2. Enter username and password
3. Check "Staff status"
4. Add appropriate permissions
5. Save

---

## 🚀 Next Steps (Optional Enhancements)

### Immediate
- [ ] Test all customer flows
- [ ] Test all staff functions
- [ ] Print and laminate QR codes
- [ ] Place QR codes on tables

### Short Term
- [ ] Customize restaurant name and branding
- [ ] Add more menu items
- [ ] Upload food images
- [ ] Adjust prices and availability
- [ ] Create additional tables

### Medium Term
- [ ] Payment processing integration (Stripe, Square)
- [ ] Email notifications
- [ ] SMS order alerts
- [ ] Kitchen display system (large monitor)
- [ ] Inventory management

### Long Term
- [ ] Customer loyalty program
- [ ] Advanced analytics
- [ ] Reservation system
- [ ] Multi-location support
- [ ] Mobile app

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Customer)                    │
│  Scans QR → Menu → Add Items → Cart → Order → Receipt   │
└────────────────────────┬────────────────────────────────┘
                         ↓
        ┌────────────────────────────────────┐
        │      Django Web Application         │
        │  ├─ URLs & Routing                  │
        │  ├─ Views & Logic                   │
        │  └─ Templates & Static Files        │
        └────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────────┐
        │      Database (SQLite)              │
        │  ├─ Categories & Menu Items         │
        │  ├─ Tables with QR Codes            │
        │  ├─ Orders & Order Items            │
        │  └─ Users & Authentication          │
        └────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              BROWSER (Staff Dashboard)                   │
│  Dashboard → Orders → Menu → Reports                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 File Structure Reference

```
burgerbills/
├── manage.py                          # Main management script
├── db.sqlite3                         # Database file
├── setup_data.py                      # Sample data script
├── README.md                          # Full documentation
├── QUICKSTART.md                      # This file
├── burgerbills/
│   ├── settings.py                    # Configuration
│   ├── urls.py                        # Main routing
│   └── wsgi.py
├── menu/
│   ├── models.py                      # 5 database models
│   ├── views.py                       # 17 view functions
│   ├── admin.py                       # Admin configuration
│   ├── urls.py                        # App routing
│   └── migrations/
│       └── 0001_initial.py
├── templates/menu/
│   ├── base.html                      # Base template
│   ├── index.html                     # Home
│   ├── customer_menu.html             # Menu display
│   ├── cart.html                      # Shopping cart
│   ├── order_status.html              # Order tracking
│   ├── receipt.html                   # Receipt
│   ├── dashboard.html                 # Staff dashboard
│   ├── all_orders.html                # Orders list
│   ├── menu_management.html           # Menu mgmt
│   └── reports.html                   # Reports
├── static/                            # Static files (CSS, JS, images)
└── venv/                              # Virtual environment
```

---

## 🆘 Troubleshooting

### Server won't start?
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
python manage.py runserver 0.0.0.0:8080
```

### Can't access admin?
- Verify superuser exists
- Check username/password spelling
- Ensure `http://localhost:8000/admin/` is exact URL

### QR codes not showing?
- Ensure media directory exists
- Check Pillow is installed: `pip list | grep Pillow`
- Check file permissions

### Static files not loading?
- Run: `python manage.py collectstatic --noinput`
- Check STATIC_ROOT in settings.py

### Database errors?
- Run: `python manage.py migrate`
- Check db.sqlite3 exists and is readable

---

## 📞 Support Resources

1. **Django Documentation**: https://docs.djangoproject.com/
2. **QRCode Library**: https://github.com/lincolnloop/python-qrcode
3. **Bootstrap Docs**: https://getbootstrap.com/docs/
4. **Python**: https://python.org/docs/

---

## 🎉 You're All Set!

Your restaurant ordering system is ready to go! 

**Next Action**: 
1. ✅ Verify server is running (`http://localhost:8000`)
2. ✅ Test a customer order at `http://localhost:8000/table/1/menu/`
3. ✅ Check dashboard at `http://localhost:8000/dashboard/` (admin/admin123)
4. ✅ Print QR codes and place on tables
5. ✅ Start taking orders!

### Quick Command Reference
```bash
# Activate environment
source venv/bin/activate

# Start server
python manage.py runserver

# Access Admin
# Username: admin
# Password: admin123
```

**Happy ordering! 🍔✨**
