"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django.contrib import admin
from .models import Category, MarqueeSettings, MenuItem, Table, Order, OrderItem


@admin.register(MarqueeSettings)
class MarqueeSettingsAdmin(admin.ModelAdmin):
    fields = ('customer_message', 'staff_message')

    def has_add_permission(self, request):
        return not MarqueeSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    list_editable = ('order',)
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'is_vegetarian', 'is_vegan', 'is_spicy', 'is_gluten_free')
    list_filter = ('category', 'is_available', 'is_vegetarian', 'is_vegan', 'is_spicy', 'is_gluten_free')
    list_editable = ('price', 'is_available')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Item Information', {
            'fields': ('category', 'name', 'description', 'image')
        }),
        ('Pricing', {
            'fields': ('price', 'has_sizes', 'size_small_price', 'size_medium_price', 'size_large_price'),
            'description': 'Enable "has_sizes" to offer size options (S, M, L) with different prices'
        }),
        ('Dietary Tags', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_spicy', 'is_gluten_free')
        }),
        ('Attributes', {
            'fields': ('is_available', 'rating')
        }),
        ('Organization', {
            'fields': ('order',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'qr_code')
    fieldsets = (
        ('Table Information', {
            'fields': ('number', 'capacity', 'is_active')
        }),
        ('QR Code', {
            'fields': ('qr_code',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'unit_price', 'created_at')
    can_delete = False
    fields = ('menu_item', 'quantity', 'unit_price', 'special_requests', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'table', 'order_type', 'status', 'total_amount', 'customer_name', 'created_at')
    list_filter = ('status', 'order_type', 'created_at', 'table')
    search_fields = ('order_number', 'table__number', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = ('order_number', 'created_at', 'updated_at', 'completed_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'order_type', 'table', 'status', 'total_amount', 'estimated_time')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Notes', {
            'fields': ('special_instructions',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj:
            # Make order_number and table read-only for existing orders
            return readonly + ('table',)
        return readonly


admin.site.site_header = "Burger Bills Admin"
admin.site.site_title = "Restaurant Admin Portal"
