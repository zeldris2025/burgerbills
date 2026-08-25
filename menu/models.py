"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings
import qrcode
import io
import uuid
from django.core.files import File
from PIL import Image


class MarqueeSettings(models.Model):
    customer_message = models.CharField(
        max_length=300,
        default="Welcome to BurgerBills • Table {table_number} • Explore our delicious menu and enjoy seamless ordering",
        help_text="Use {table_number} to display the customer's table number.",
    )
    staff_message = models.CharField(
        max_length=300,
        default="New Beef Gyro • Buy 2, Get 1 Free • New Chicken Gyro",
    )

    @classmethod
    def load(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Marquee settings"

    class Meta:
        verbose_name_plural = "Marquee settings"


class Category(models.Model):
    """Menu categories like Burgers, Drinks, Sides, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='🍔', help_text="Emoji or icon name")
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Individual menu items"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    # Dietary tags
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    
    rating = models.FloatField(default=0.0)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Size options
    has_sizes = models.BooleanField(default=False, help_text="Enable size options (S, M, L)")
    size_small_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Price for small size")
    size_medium_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Price for medium size")
    size_large_price = models.DecimalField(max_digits=8, decimal_places=2, default=0, help_text="Price for large size")

    class Meta:
        ordering = ['category', 'order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
        ]

    def __str__(self):
        return f"{self.name} - ${self.price}"
    
    def get_dietary_tags(self):
        """Return list of dietary tags for this item"""
        tags = []
        if self.is_vegan:
            tags.append('Vegan')
        elif self.is_vegetarian:
            tags.append('Vegetarian')
        if self.is_spicy:
            tags.append('Spicy')
        if self.is_gluten_free:
            tags.append('Gluten-Free')
        return tags

    def get_sizes(self):
        """Return size options if available (only non-zero prices)"""
        if self.has_sizes:
            sizes = {}
            if self.size_small_price > 0:
                sizes['S'] = {'label': 'Small', 'price': float(self.size_small_price)}
            if self.size_medium_price > 0:
                sizes['M'] = {'label': 'Medium', 'price': float(self.size_medium_price)}
            if self.size_large_price > 0:
                sizes['L'] = {'label': 'Large', 'price': float(self.size_large_price)}
            return sizes if sizes else None
        return None


class Table(models.Model):
    """Restaurant tables"""
    number = models.IntegerField(unique=True)
    capacity = models.IntegerField(default=4)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_access_token = models.UUIDField(default=uuid.uuid4, editable=False)
    qr_code_generated_at = models.DateTimeField(default=timezone.now, help_text="Timestamp when QR code was last generated")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Security: Menu access expires after this many minutes of inactivity
    menu_access_timeout_minutes = models.IntegerField(
        default=60,
        help_text="Customer menu access expires after this many minutes of inactivity"
    )

    def __str__(self):
        return f"Table {self.number}"

    def save(self, *args, **kwargs):
        qr_code_missing = not self.qr_code or not self.qr_code.storage.exists(self.qr_code.name)
        if qr_code_missing:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.get_qr_menu_url())
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            filename = f'qr_code_table_{self.number}.png'
            storage_name = self.qr_code.field.generate_filename(self, filename)
            self.qr_code.storage.delete(storage_name)
            buffer = io.BytesIO()
            img.save(buffer, 'PNG')
            buffer.seek(0)
            self.qr_code.save(filename, File(buffer), save=False)

        super().save(*args, **kwargs)

    def get_qr_menu_url(self):
        base_url = settings.QR_CODE_BASE_URL.rstrip('/')
        return f"{base_url}/table/{self.number}/menu/?access={self.qr_access_token}"

    class Meta:
        ordering = ['number']


class Order(models.Model):
    """Customer orders"""
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    ORDER_TYPE_CHOICES = [
        ('dine_in', 'Dine In'),
        ('pickup', 'Pickup'),
    ]

    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='dine_in')
    
    # Customer info
    customer_name = models.CharField(max_length=200, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_instructions = models.TextField(blank=True)
    estimated_time = models.IntegerField(default=20, help_text="Estimated time in minutes")
    
    is_called = models.BooleanField(default=False, help_text="Customer has been called to pick up")
    called_at = models.DateTimeField(blank=True, null=True)
    cart_expires_at = models.DateTimeField(blank=True, null=True, help_text="Cart auto-expires after 5 minutes of inactivity")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.table:
            return f"Order {self.order_number} - Table {self.table.number}"
        return f"Order {self.order_number} - {self.get_order_type_display()}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import random
            self.order_number = f"ORD-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # Set cart expiry time if it's a pending order
        if self.status == 'pending' and not self.cart_expires_at:
            from datetime import timedelta
            self.cart_expires_at = timezone.now() + timedelta(minutes=5)
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    special_requests = models.TextField(blank=True, help_text="e.g., No onions, Extra cheese")
    created_at = models.DateTimeField(auto_now_add=True)

    def get_subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        item_name = self.menu_item.name if self.menu_item else "Deleted menu item"
        return f"{self.quantity}x {item_name}"

    class Meta:
        ordering = ['created_at']


