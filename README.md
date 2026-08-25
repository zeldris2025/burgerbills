# Burger Bills - Modern QR Code Restaurant Ordering System

## 🎉 System Overview

Burger Bills is a fully automated, modern restaurant ordering system where customers scan QR codes at tables to access a beautiful menu, place orders, and track their order status in real-time. Staff can manage the kitchen operations from a professional dashboard.

## ✨ Features

### Customer Features
- **QR Code Scanning** - Each table has a unique QR code linking to the menu
- **Modern Menu Interface** - Professional, restaurant-quality UI with category browsing
- **Shopping Cart** - Add items, manage quantities, add special requests
- **Order Tracking** - Real-time order status updates (Pending → Preparing → Ready → Completed)
- **Receipt Generation** - Printable receipts for each order
- **Mobile Responsive** - Works perfectly on phones, tablets, and desktops

### Staff/Admin Features
- **Cashier Dashboard** - Real-time order management with quick status updates
- **Order Management** - View, filter, and update order statuses
- **Menu Management** - Add/edit menu items and manage inventory
- **Sales Reports** - Daily revenue, popular items, and analytics
- **Admin Panel** - Full Django admin for comprehensive management

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip and virtual environment support

### Installation

1. **Navigate to project directory**:
   ```bash
   cd /Users/nagaseufamily/Downloads/burgerbills
   ```

2. **Activate virtual environment** (if not already active):
   ```bash
   source venv/bin/activate
   ```

3. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

The application will be available at: `http://localhost:8000`

## 📱 Using the System

### For Customers

1. **Scan QR Code**: Look for the QR code on your table
2. **Browse Menu**: Explore categories and menu items
3. **Add to Cart**: Click "Add" button and select quantity + special requests
4. **Review Cart**: Go to your cart to see all items
5. **Submit Order**: Click "Submit Order" to send to kitchen
6. **Track Order**: Watch real-time status updates
7. **View Receipt**: See your receipt and total amount

### For Staff

#### Access Admin Panel
- **URL**: `http://localhost:8000/admin/`
- **Username**: `admin`
- **Password**: `admin123`

#### Dashboard
- **URL**: `http://localhost:8000/dashboard/`
- View pending orders
- See today's revenue
- Quick status updates for active orders

#### Orders Management
- **URL**: `http://localhost:8000/orders/`
- Filter by status (Pending, Confirmed, Preparing, Ready, Completed)
- View order details and items

#### Menu Management
- **URL**: `http://localhost:8000/menu-management/`
- View all menu items by category
- Quick access to edit items
- See availability status

#### Reports
- **URL**: `http://localhost:8000/reports/`
- Daily sales statistics
- Top-selling items
- Performance metrics

## 🗂️ Project Structure

```
burgerbills/
├── manage.py                 # Django management script
├── burgerbills/             # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI configuration
├── menu/                    # Main application
│   ├── models.py            # Database models
│   ├── views.py             # View logic
│   ├── admin.py             # Admin configuration
│   ├── urls.py              # App URL routing
│   └── migrations/          # Database migrations
├── templates/               # HTML templates
│   └── menu/
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── customer_menu.html    # Menu display
│       ├── cart.html             # Shopping cart
│       ├── order_status.html      # Order tracking
│       ├── receipt.html           # Receipt
│       ├── dashboard.html         # Staff dashboard
│       ├── all_orders.html        # Orders list
│       ├── menu_management.html   # Menu management
│       └── reports.html           # Reports/analytics
└── db.sqlite3               # Database file
```

## 🗄️ Database Models

### Category
Menu item categories (Burgers, Drinks, Sides, Desserts, etc.)

### MenuItem
Individual menu items with:
- Name, description, price
- Image upload support
- Availability status
- Vegetarian/Spicy tags
- Rating system

### Table
Restaurant tables with:
- Table number
- Capacity
- Auto-generated QR code
- Active status

### Order
Customer orders with:
- Order number (auto-generated)
- Status tracking (Pending → Completed)
- Table reference
- Total amount
- Special instructions

### OrderItem
Individual items in an order with:
- Menu item reference
- Quantity
- Unit price
- Special requests (no onions, extra cheese, etc.)

## 🔐 Admin Panel Features

### User Management
- Create staff users for orders, menu management, and reports

### Menu Management
- Add/edit categories
- Add/edit menu items with images
- Mark items as available/unavailable
- Set prices and ratings

### Order Management
- View all orders with filtering
- Update order status
- See order items and special requests
- Track completion times

### Table Management
- Create/edit restaurant tables
- Auto-generate QR codes
- Set table capacity

## 🎨 Customization

### Updating Colors
Edit the CSS in `templates/menu/base.html`:
```css
:root {
    --primary-color: #FF6B35;      /* Orange */
    --secondary-color: #004E89;    /* Dark Blue */
    --accent-color: #F7931E;       /* Light Orange */
}
```

### Adding New Categories
1. Go to Admin Panel (`/admin/`)
2. Click "Categories" → "Add Category"
3. Enter name, description, emoji icon
4. Save

### Adding Menu Items
1. Go to Admin Panel (`/admin/`)
2. Click "Menu Items" → "Add Menu Item"
3. Fill in details, upload image (optional)
4. Set price and availability
5. Save

### Creating Tables
1. Go to Admin Panel (`/admin/`)
2. Click "Tables" → "Add Table"
3. Enter table number and capacity
4. Save (QR code auto-generates)

## 🔧 Common Tasks

### View Today's Orders
1. Go to Dashboard `/dashboard/`
2. See all active orders with auto-update

### Mark Order as Complete
1. Dashboard or Orders page
2. Click appropriate status button
3. Order automatically updates

### Change Item Availability
1. Admin Panel → Menu Items
2. Click "Edit" on item
3. Toggle "Is Available" checkbox
4. Save

### Generate QR Codes for Tables
- QR codes are auto-generated when tables are created
- Download from Admin Panel's Table management
- Print and laminate for durability

## 📊 Order Flow

```
Customer scans QR code
        ↓
Accesses menu for their table
        ↓
Adds items to cart with special requests
        ↓
Reviews cart and submits order
        ↓
Order sent to kitchen (Status: Confirmed)
        ↓
Kitchen starts preparing (Status: Preparing)
        ↓
Order ready (Status: Ready)
        ↓
Customer collects order
        ↓
Marked as completed (Status: Completed)
        ↓
Receipt generated for payment
```

## 🎯 Security Features

- CSRF protection on all forms
- Database-level constraints
- Admin authentication required for staff functions
- Session-based security
- Table number validation through QR codes

## 📈 Performance

- Fast database queries with proper indexing
- Optimized images and static files
- Real-time updates without page refresh (AJAX)
- Auto-refresh dashboards for fresh data
- Responsive design for all devices

## 🐛 Troubleshooting

### QR Codes not generating
- Ensure `media/` directory exists
- Check file permissions on the directory
- Verify Pillow is installed: `pip install pillow`

### Static files not loading
- Run: `python manage.py collectstatic`
- Check STATIC_ROOT setting in settings.py

### Database errors
- Run: `python manage.py migrate`
- Check db.sqlite3 permissions

### Admin panel not accessible
- Verify superuser exists: `python manage.py createsuperuser`
- Check login credentials

## 📞 Support

For issues or questions:
1. Check Django documentation: https://docs.djangoproject.com/
2. Review QRCode library: https://github.com/lincolnloop/python-qrcode
3. Check project logs for error messages

## 📝 License

This project is designed for restaurant use. Modify and deploy as needed for your business.

## 🌟 Future Enhancements

- Payment processing integration
- Multi-language support
- Customer loyalty program
- Reservation system
- Kitchen display system (KDS)
- Advanced analytics and reports
- Email/SMS notifications
- Inventory management
- Printer integration for receipts
- Customer feedback/ratings system

---

**Version**: 1.0  
**Last Updated**: 2024  
**Built with**: Django, Bootstrap, Python

Enjoy running your modern restaurant with Burger Bills! 🍔✨
