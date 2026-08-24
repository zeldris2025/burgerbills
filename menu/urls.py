"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('media/qr_codes/qr_code_table_<int:table_number>.png', views.table_qr_code, name='table_qr_code'),

    # Customer views
    path('', views.index, name='index'),
    path('table/<int:table_number>/menu/', views.table_menu, name='table_menu'),
    path('table/<int:table_number>/session-time/', views.session_time, name='session_time'),
    path('table/<int:table_number>/debug-session/', views.debug_session, name='debug_session'),
    path('table/<int:table_number>/add/', views.add_to_order, name='add_to_order'),
    path('table/<int:table_number>/add-to-order/', views.add_to_order, name='add_to_order_alt'),
    path('table/<int:table_number>/update-item-notes/', views.update_item_notes, name='update_item_notes'),
    path('table/<int:table_number>/orders/', views.current_order_items, name='current_order_items'),
    path('table/<int:table_number>/update/<int:item_id>/', views.update_order_item, name='update_order_item'),
    path('table/<int:table_number>/cart/', views.view_cart, name='view_cart'),
    path('table/<int:table_number>/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('table/<int:table_number>/checkout/', views.checkout, name='checkout'),
    path('table/<int:table_number>/submit/', views.submit_order, name='submit_order'),
    path('table/<int:table_number>/order/<int:order_id>/', views.order_status, name='order_status'),
    path('table/<int:table_number>/order/<int:order_id>/status/', views.order_status_data, name='order_status_data'),
    path('table/<int:table_number>/order/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    path('table/<int:table_number>/order/<int:order_id>/receipt/', views.receipt, name='receipt'),

    # Admin/Cashier views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.all_orders, name='all_orders'),
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('order/<int:order_id>/call-customer/', views.call_customer, name='call_customer'),
    path('menu-management/', views.menu_management, name='menu_management'),
    path('reports/', views.reports, name='reports'),

    # Staff login & panel routes
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),
    path('staff/panel/', views.staff_panel, name='staff_panel'),
    path('staff/order/<int:order_id>/receipt/', views.staff_order_receipt, name='staff_order_receipt'),
    path('staff/order/<int:order_id>/update-status/', views.staff_update_status, name='staff_update_status'),
    path('staff/order/<int:order_id>/call-customer/', views.staff_call_customer, name='staff_call_customer'),

    # Manager login & staff management routes
    path('manager/login/', views.manager_login, name='manager_login'),
    path('manager/logout/', views.manager_logout, name='manager_logout'),
    path('manager/panel/', views.manager_panel, name='manager_panel'),
    path('manager/create-staff-user/', views.create_staff_user, name='create_staff_user'),
    path('manager/delete-staff-user/<int:user_id>/', views.delete_staff_user, name='delete_staff_user'),
]
