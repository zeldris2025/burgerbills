"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .menu_transfer import MenuImportError, export_csv, export_zip, import_menu
from .models import Category, MarqueeSettings, MenuItem, Table, Order, OrderItem, Promotion


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


class MenuImportForm(forms.Form):
    file = forms.FileField(
        label='Menu file',
        help_text='A .zip exported from this panel (includes photos), or a .csv file.',
    )


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    change_list_template = 'admin/menu/menuitem/change_list.html'
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

    def get_urls(self):
        return [
            path('export/', self.admin_site.admin_view(self.export_view), name='menu_menuitem_export'),
            path('import/', self.admin_site.admin_view(self.import_view), name='menu_menuitem_import'),
        ] + super().get_urls()

    def export_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        stamp = timezone.localtime().strftime('%Y-%m-%d')
        if request.GET.get('format') == 'csv':
            response = HttpResponse(export_csv(), content_type='text/csv; charset=utf-8')
            filename = f'burgerbills-menu-{stamp}.csv'
        else:
            response = HttpResponse(export_zip(), content_type='application/zip')
            filename = f'burgerbills-menu-{stamp}.zip'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def import_view(self, request):
        if not (self.has_add_permission(request) and self.has_change_permission(request)):
            raise PermissionDenied
        form = MenuImportForm(request.POST or None, request.FILES or None)
        import_errors = []
        if request.method == 'POST' and form.is_valid():
            try:
                counts = import_menu(form.cleaned_data['file'])
            except MenuImportError as exc:
                import_errors = exc.errors
            else:
                messages.success(
                    request,
                    f"Import complete: {counts['created']} item(s) added, {counts['updated']} updated, "
                    f"{counts['categories_created']} new categor{'y' if counts['categories_created'] == 1 else 'ies'}.",
                )
                return redirect('admin:menu_menuitem_changelist')
        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Import menu items',
            'form': form,
            'import_errors': import_errors,
        }
        return TemplateResponse(request, 'admin/menu/menuitem/import.html', context)


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


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'starts_at', 'ends_at', 'is_published', 'display_order')
    list_filter = ('is_published',)
    list_editable = ('is_published', 'display_order')
    search_fields = ('title', 'tagline', 'description')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
