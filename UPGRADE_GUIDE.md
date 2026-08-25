# BurgerBills - Modern Restaurant Menu Application

A beautiful, fully responsive digital menu system for restaurants with real-time ordering, cart management, and order tracking.

## 🎯 Features

### Customer Experience
- ✨ **Modern Responsive Design** - Beautiful UI that works seamlessly on desktop, tablet, and mobile devices
- 🎨 **Smooth Animations** - Elegant fade-ins, slide transitions, and hover effects
- 🛒 **Smart Shopping Cart** - Floating sidebar cart with real-time updates
- 📱 **Mobile-Optimized** - Bottom sheet cart on mobile, full sidebar on desktop
- 🔍 **Easy Navigation** - Category tabs with smooth scrolling and automatic highlighting
- 🏷️ **Dietary Information** - Clear badges for Vegan, Vegetarian, Spicy, and Gluten-Free items
- ⭐ **Order Tracking** - Real-time order status updates
- 📋 **Special Requests** - Add custom instructions to menu items

### Design & UX
- 🎯 **Premium Color Scheme** - Elegant dark theme with warm accent colors
- 💫 **Micro-interactions** - Bouncing animations on buttons, pulsing cart badges
- 📸 **Beautiful Cards** - Hover effects with image zoom and card lift
- 🎬 **Page Load Animations** - Staggered fade-in effects for menu items
- 📊 **Visual Hierarchy** - Clear typography and spacing throughout

### Technical Features
- 🔒 **CSRF Protection** - Secure form submission
- 📡 **AJAX Integration** - Smooth server communication without page reloads
- 🍃 **Django Admin** - Enhanced admin interface for staff
- 📊 **Order Management** - Dashboard for staff and managers
- 📈 **Reports & Analytics** - Sales tracking and popular item reports

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Django 2.2+
- pip

### Installation

1. **Navigate to project directory:**
```bash
cd burgerbills
```

2. **Install dependencies:**
```bash
pip install django pillow qrcode
```

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Load sample data:**
```bash
python manage.py load_sample_data
```

5. **Create superuser (for admin):**
```bash
python manage.py createsuperuser
```

6. **Start development server:**
```bash
python manage.py runserver
```

7. **Access the application:**
   - Customer Menu: http://localhost:8000/table/1/menu/
   - Admin Panel: http://localhost:8000/admin/
   - Dashboard: http://localhost:8000/dashboard/

## 📁 Project Structure

```
burgerbills/
├── static/
│   ├── css/
│   │   └── style.css           # Main modern stylesheet
│   ├── images/
│   └── js/
│       ├── animations.js        # Smooth animations & transitions
│       └── cart.js              # Shopping cart functionality
├── templates/
│   └── menu/
│       ├── base_modern.html           # Modern base template
│       ├── customer_menu_modern.html  # Modern menu view
│       ├── checkout_modern.html       # Modern checkout page
│       ├── order_confirmation_modern.html # Order confirmation
│       └── [legacy templates]
├── menu/
│   ├── models.py               # Database models
│   ├── views.py                # View logic
│   ├── urls.py                 # URL routing
│   ├── admin.py                # Admin configuration
│   └── management/
│       └── commands/
│           └── load_sample_data.py # Sample data loader
├── manage.py
└── db.sqlite3
```

## 🎨 Modern Design Features

### Color Scheme
- **Primary Dark**: `#1a1a1a` - Professional dark background
- **Accent Color**: `#d4a574` - Warm gold/brown for highlights
- **Primary Light**: `#f8f8f8` - Clean light backgrounds

### Typography
- **Display Font**: Playfair Display - Elegant and professional
- **Body Font**: Inter - Clean and readable

### Responsive Breakpoints
- Desktop: Full-width layout with sidebar cart
- Tablet (max-width: 1024px): Adjusted grid and spacing
- Mobile (max-width: 768px): Stacked layout with bottom sheet cart
- Small Mobile (max-width: 480px): Optimized for small screens

## 📱 Key Pages

### Customer Menu (Modern Design)
- Full-screen hero section with welcome message
- Category navigation with smooth scrolling
- Menu grid with beautiful item cards
- Floating add-to-cart buttons
- Dietary badge indicators
- Smooth stagger animations on load

**URL:** `/table/<table_number>/menu/`

### Checkout
- Order summary with itemized list
- Customer information form
- Service type selection (Dine-in or Pickup)
- Special instructions textarea
- Estimated time selection
- Modern form design with smooth interactions

**URL:** `/table/<table_number>/checkout/`

### Order Confirmation
- Success confirmation with visual feedback
- Order number and timing details
- Service type and estimated time display
- Customer information summary
- Order status timeline
- Auto-refresh every 10 seconds
- Links to add more items or refresh status

**URL:** `/table/<table_number>/order/<order_id>/confirmation/`

## 🛒 Shopping Cart Features

### Desktop Experience
- Fixed right sidebar cart (400px wide)
- Smooth slide-in animation on open
- Real-time item count badge
- Quantity controls with +/- buttons
- Item removal with confirmation
- Running total calculation
- "Proceed to Checkout" button

### Mobile Experience
- Bottom sheet modal cart (90vh max height)
- Full-width swipe-friendly interface
- Easier thumb reach for controls
- Maintains same functionality as desktop

### Cart Functionality
- Add items with quantity selection
- Update quantities with buttons
- Remove items from cart
- Auto-save to server
- 5-minute cart expiration on server
- Toast notifications for user feedback

## 🍔 Dietary Tags

Each menu item can be tagged with:
- 🌱 **Vegan** - Plant-based, no animal products
- 🥗 **Vegetarian** - No meat, may contain dairy
- 🌶️ **Spicy** - Contains hot peppers
- 🍞 **Gluten-Free** - No gluten products

Tags appear as colorful badges on menu items with distinct colors for quick identification.

## ⚙️ Database Models

### Category
- `name` - Category name (e.g., "Burgers")
- `description` - Category description
- `icon` - Emoji or icon (e.g., "🍔")
- `order` - Display order

### MenuItem
- `category` - Foreign key to Category
- `name` - Item name
- `description` - Item description
- `price` - Item price
- `image` - Optional food image
- `is_available` - Availability flag
- `is_vegetarian` - Vegetarian tag
- `is_vegan` - Vegan tag
- `is_spicy` - Spicy tag
- `is_gluten_free` - Gluten-free tag
- `rating` - Average rating (0-5)
- `order` - Display order

### Order
- `table` - Foreign key to Table (for dine-in)
- `order_number` - Unique order ID (auto-generated)
- `order_type` - "dine_in" or "pickup"
- `status` - pending/confirmed/preparing/ready/completed/cancelled
- `customer_name` - Customer name
- `customer_phone` - Customer phone
- `customer_email` - Customer email
- `total_amount` - Order total
- `special_instructions` - Special requests
- `estimated_time` - Estimated preparation time in minutes
- `is_called` - Whether customer has been called
- `cart_expires_at` - Auto-expiration time for pending carts

### OrderItem
- `order` - Foreign key to Order
- `menu_item` - Foreign key to MenuItem
- `quantity` - Quantity ordered
- `unit_price` - Price at time of order
- `special_requests` - Item-specific requests

### Table
- `number` - Table number
- `capacity` - Seating capacity
- `qr_code` - Generated QR code image
- `is_active` - Active status

## 🔐 Authentication & Authorization

### Customer Access
- No authentication required
- Table number in URL identifies session
- Orders tied to table/session

### Staff Access
- Login required (`/staff/login/`)
- Can view and update orders
- Can call customers
- Limited to order management

### Manager Access
- Login required (`/manager/login/`)
- Full admin access
- Can manage staff users
- Can view reports and analytics

## 🎬 JavaScript Features

### CartManager Class
Handles all cart operations:
```javascript
const cartManager = new CartManager(tableNumber);
cartManager.addToCart(itemId);
cartManager.updateQuantity(itemId, 'increase');
cartManager.removeFromCart(itemId);
cartManager.checkout();
```

### MenuAnimations Class
Manages page animations:
- Page load fade-in
- Stagger item animations
- Category tab scrolling
- Hover effects
- Smooth scrolling behavior

### Toast Notifications
User feedback system:
```javascript
showToast(message, 'success'); // Green
showToast(message, 'error');   // Red
showToast(message, 'info');    // Blue
```

## 🎨 CSS Features

### Animations
- `fadeIn` - Smooth opacity transition
- `slideInUp` - Slide up from bottom
- `slideInRight` - Slide in from right
- `scaleIn` - Zoom in effect
- `pulse` - Pulsing opacity
- `bounce` - Bounce animation
- `slideInLeft` - Slide from left

### Utility Classes
- `.fade-in`, `.slide-up`, `.scale-in` - Animation classes
- `.hidden`, `.visible` - Display utilities
- `.text-muted`, `.text-accent` - Text colors
- `.d-flex`, `.justify-between` - Flexbox utilities
- `.gap-sm`, `.gap-md`, `.gap-lg` - Gap utilities
- `.mt`, `.mb`, `.my`, `.px` - Margin/padding utilities

## 📊 Sample Data

The `load_sample_data` command creates:
- **8 Categories**: Burgers, Sandwiches, Appetizers, Salads, Pizza, Pasta, Desserts, Drinks
- **30+ Menu Items**: Various food items with dietary tags
- **10 Tables**: Pre-configured dining tables

Run anytime to refresh sample data:
```bash
python manage.py load_sample_data
```

## 🔗 API Endpoints

### Customer Endpoints
- `GET /table/<table>/menu/` - View menu
- `POST /table/<table>/add/` - Add to cart (JSON)
- `POST /table/<table>/update/<item_id>/` - Update quantity (JSON)
- `POST /table/<table>/remove/<item_id>/` - Remove from cart
- `GET /table/<table>/checkout/` - Checkout page
- `POST /table/<table>/checkout/` - Submit checkout form
- `GET /table/<table>/order/<order_id>/confirmation/` - Order confirmation

### Staff Endpoints
- `GET /dashboard/` - Staff dashboard
- `GET /orders/` - All orders list
- `POST /order/<order_id>/update-status/` - Update status (JSON)
- `POST /order/<order_id>/call-customer/` - Call customer (JSON)

## 🚀 Deployment

### Production Checklist
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Collect static files: `python manage.py collectstatic`
5. Use a production database (PostgreSQL recommended)
6. Set up HTTPS/SSL
7. Configure email for order notifications
8. Set up proper logging

### Deployment Commands
```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn burgerbills.wsgi:application
```

## 🐛 Troubleshooting

### Cart not showing items
- Check browser's localStorage/sessionStorage
- Verify CSRF token in forms
- Check browser console for JavaScript errors

### Images not displaying
- Ensure media files are properly configured
- Run `python manage.py collectstatic`
- Check file permissions on media directory

### Animations not working
- Verify CSS/JS files are loaded (check Network tab)
- Ensure static files are served correctly
- Check browser console for any errors

## 📝 Customization

### Change Colors
Edit CSS variables in `static/css/style.css`:
```css
:root {
  --primary-dark: #1a1a1a;
  --accent-color: #d4a574;
  --primary-light: #f8f8f8;
}
```

### Add New Features
1. Create model in `models.py`
2. Add view in `views.py`
3. Create template in `templates/menu/`
4. Add URL pattern in `urls.py`
5. Register in admin.py if needed

### Modify Templates
- Base template: `base_modern.html`
- Customer menu: `customer_menu_modern.html`
- Checkout: `checkout_modern.html`
- Order confirmation: `order_confirmation_modern.html`

## 📞 Support & Help

For issues or questions:
1. Check the troubleshooting section above
2. Review Django documentation: https://docs.djangoproject.com
3. Check console for error messages
4. Verify all dependencies are installed

## 📄 License

This project is available for use and modification.

## 🎓 Learning Resources

- Django Official Docs: https://docs.djangoproject.com
- CSS Grid & Flexbox: https://developer.mozilla.org/en-US/docs/Web/CSS
- JavaScript Classes: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes
- Web Animations: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations

---

**Enjoy your modern restaurant menu application!** 🍔✨
