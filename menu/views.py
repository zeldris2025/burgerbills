"""
Burger Bills - Restaurant Menu Management System
Copyright © 2026 Charlie Ah Kuoi. All rights reserved.
Proprietary and confidential. Unauthorized copying or distribution is prohibited.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_GET, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Sum, Count, Prefetch
from decimal import Decimal
import json
from datetime import datetime

from .models import Category, MarqueeSettings, MenuItem, Table, Order, OrderItem


class AccessDeniedException(Exception):
    """Custom exception for menu access denial"""
    pass


def handle_access_denied(view_func):
    """Decorator to handle AccessDeniedException and display access denied page or JSON error"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except AccessDeniedException as e:
            error_msg = str(e)
            print(f"AccessDeniedException in {view_func.__name__}: {error_msg}")
            print(f"Headers: X-Requested-With={request.headers.get('X-Requested-With')}, Method={request.method}")

            # Check if this is an AJAX/JSON request
            is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                      request.method in ['POST', 'PUT', 'DELETE'] or
                      request.headers.get('Content-Type') == 'application/json')

            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'message': error_msg
                }, status=403)
            else:
                return render(request, 'menu/access_denied.html', {
                    'error_message': error_msg,
                }, status=403)
    return wrapper


def index(request):
    """Show the public Burger Bills website without ordering entry points."""
    return render(request, 'menu/index.html')


def _get_customer_table(request, table_number):
    from datetime import timedelta

    try:
        table = get_object_or_404(Table, number=table_number, is_active=True)
    except Http404:
        raise AccessDeniedException('Table not found. Please scan the QR code at your table.')

    supplied_token = request.GET.get('access')

    # If access token is provided (from QR code), validate and create new session
    if supplied_token:
        if supplied_token == str(table.qr_access_token):
            # Valid QR code scan - create/update session
            request.session['qr_table_number'] = table.number
            request.session['qr_session_start_time'] = timezone.now().isoformat()
            request.session['qr_access_timeout_minutes'] = table.menu_access_timeout_minutes
            request.session.set_expiry(table.menu_access_timeout_minutes * 60)
        else:
            # Invalid access token
            raise AccessDeniedException('Invalid QR code. Please scan the QR code at your table.')

    # Check if user has valid session access
    if request.session.get('qr_table_number') != table.number:
        raise AccessDeniedException('Access denied. Please scan the QR code at your table to access the menu.')

    # Check if session has expired (hard timeout from initial scan time)
    session_start_str = request.session.get('qr_session_start_time')
    timeout_minutes = request.session.get('qr_access_timeout_minutes', table.menu_access_timeout_minutes)

    if session_start_str:
        from datetime import datetime as dt
        session_start = dt.fromisoformat(session_start_str)
        session_expiry = session_start + timedelta(minutes=timeout_minutes)

        if timezone.now() > session_expiry:
            # Session has expired (hard timeout)
            request.session.flush()
            raise AccessDeniedException('Your menu access has expired. Please scan the QR code at your table again.')

    return table


@require_GET
def table_qr_code(request, table_number):
    table = get_object_or_404(Table, number=table_number)
    table.save()
    return FileResponse(table.qr_code.open('rb'), content_type='image/png')


@handle_access_denied
def table_menu(request, table_number):
    """Customer menu view for a specific table - Modern responsive design"""
    from datetime import timedelta
    
    table = _get_customer_table(request, table_number)
    
    # Get all categories with their available items, ordered by order field
    categories = Category.objects.prefetch_related(
        Prefetch('items', MenuItem.objects.filter(is_available=True).order_by('order'))
    ).order_by('order')
    
    # Get active order for this table (pending only - once confirmed, it goes to kitchen)
    current_order = Order.objects.filter(
        table=table,
        status='pending'
    ).latest('created_at') if Order.objects.filter(
        table=table,
        status='pending'
    ).exists() else None

    # Check if pending cart has expired (5 minutes)
    if current_order and current_order.status == 'pending' and current_order.cart_expires_at:
        if timezone.now() > current_order.cart_expires_at:
            # Cart has expired, delete it for new customer
            current_order.delete()
            current_order = None
    
    # Refresh cart expiry time if order exists
    if current_order and current_order.status == 'pending':
        current_order.cart_expires_at = timezone.now() + timedelta(minutes=5)
        current_order.save()

    context = {
        'table': table,
        'categories': categories,
        'current_order': current_order,
        'customer_marquee': MarqueeSettings.load().customer_message.replace(
            '{table_number}', str(table.number)
        ),
    }
    return render(request, 'menu/customer_menu_fresh.html', context)


@csrf_exempt
@csrf_exempt
@handle_access_denied
@require_http_methods(["POST"])
def get_item(request, table_number):
    """Get item details including sizes"""
    try:
        table = _get_customer_table(request, table_number)
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')

        menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)

        response = {
            'id': menu_item.id,
            'name': menu_item.name,
            'price': float(menu_item.price),
            'has_sizes': menu_item.has_sizes,
            'sizes': None
        }

        if menu_item.has_sizes:
            sizes = {}
            if menu_item.size_small_price > 0:
                sizes['S'] = {
                    'label': 'Small',
                    'price': float(menu_item.size_small_price)
                }
            if menu_item.size_medium_price > 0:
                sizes['M'] = {
                    'label': 'Medium',
                    'price': float(menu_item.size_medium_price)
                }
            if menu_item.size_large_price > 0:
                sizes['L'] = {
                    'label': 'Large',
                    'price': float(menu_item.size_large_price)
                }
            response['sizes'] = sizes if sizes else None
            response['has_sizes'] = bool(sizes)

        return JsonResponse(response)

    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_GET
def debug_session(request, table_number):
    """Debug endpoint to check session status"""
    table = get_object_or_404(Table, number=table_number, is_active=True)
    supplied_token = request.GET.get('access')

    debug_info = {
        'table_number': table_number,
        'table_qr_token': str(table.qr_access_token),
        'supplied_token': supplied_token,
        'session_data': {
            'qr_table_number': request.session.get('qr_table_number'),
            'qr_session_start_time': request.session.get('qr_session_start_time'),
            'qr_access_timeout_minutes': request.session.get('qr_access_timeout_minutes'),
        },
        'token_match': supplied_token == str(table.qr_access_token) if supplied_token else None,
        'session_key': request.session.session_key,
    }

    return JsonResponse(debug_info)


@require_GET
def session_time(request, table_number):
    """Get remaining session time for the table menu"""
    from datetime import datetime as dt

    try:
        table = _get_customer_table(request, table_number)
    except AccessDeniedException:
        return JsonResponse({'error': 'Invalid or expired session'}, status=403)

    # Get session expiry information
    session_start_str = request.session.get('qr_session_start_time')
    timeout_minutes = request.session.get('qr_access_timeout_minutes', table.menu_access_timeout_minutes)

    if session_start_str:
        session_start = dt.fromisoformat(session_start_str)
        expiry_time = session_start + timezone.timedelta(minutes=timeout_minutes)
        expires_in = int((expiry_time - timezone.now()).total_seconds())

        # Ensure it doesn't go negative
        expires_in = max(0, expires_in)

        return JsonResponse({
            'expires_in': expires_in,
            'timeout_minutes': timeout_minutes,
            'session_start_time': session_start_str,
            'expiry_time': expiry_time.isoformat(),
        })
    else:
        return JsonResponse({'error': 'No active session'}, status=403)


@csrf_exempt
@handle_access_denied
@require_http_methods(["POST"])
def add_to_order(request, table_number):
    """Add item to order via AJAX"""
    from datetime import timedelta

    table = _get_customer_table(request, table_number)

    try:
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')
        quantity = int(data.get('quantity', 1))
        special_requests = data.get('special_requests', '').strip()
        unit_price = data.get('unit_price')  # Size-specific price from frontend

        menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)

        # Use provided unit_price or fall back to menu item's default price
        if unit_price is not None:
            try:
                unit_price = Decimal(str(unit_price))
            except (ValueError, TypeError):
                unit_price = menu_item.price
        else:
            unit_price = menu_item.price

        # Get or create current order
        order, created = Order.objects.get_or_create(
            table=table,
            status='pending',
            defaults={'total_amount': 0}
        )

        # Check if pending cart has expired
        if order.cart_expires_at and timezone.now() > order.cart_expires_at:
            order.delete()
            order, created = Order.objects.get_or_create(
                table=table,
                status='pending',
                defaults={'total_amount': 0}
            )

        # Check if item already in order (include unit_price in lookup to distinguish size variants)
        order_item, item_created = OrderItem.objects.get_or_create(
            order=order,
            menu_item=menu_item,
            unit_price=unit_price,
            special_requests=special_requests,
            defaults={'quantity': quantity}
        )

        if not item_created:
            order_item.quantity += quantity
            order_item.save()

        # Update order total and refresh cart expiry
        order.total_amount = sum(
            item.quantity * item.unit_price 
            for item in order.items.all()
        )
        order.cart_expires_at = timezone.now() + timedelta(minutes=5)
        order.save()

        return JsonResponse({
            'success': True,
            'message': f'{menu_item.name} added to order!',
            'order_id': order.id,
            'total_items': sum(item.quantity for item in order.items.all()),
            'total_amount': str(order.total_amount),
        })

    except MenuItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in add_to_order: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=400)


@csrf_exempt
@handle_access_denied
@require_http_methods(["POST"])
def update_item_notes(request, table_number):
    """Update special requests for an order item"""
    table = _get_customer_table(request, table_number)

    try:
        data = json.loads(request.body)
        menu_item_id = data.get('menu_item_id')
        special_requests = data.get('special_requests', '').strip()

        # Get the pending order
        order = Order.objects.filter(table=table, status='pending').first()
        if not order:
            return JsonResponse({'success': False, 'message': 'No pending order'}, status=404)

        # Find and update the order item
        order_item = order.items.filter(menu_item_id=menu_item_id).first()
        if order_item:
            order_item.special_requests = special_requests
            order_item.save()
            return JsonResponse({'success': True, 'message': 'Notes updated'})
        else:
            return JsonResponse({'success': False, 'message': 'Item not in order'}, status=404)

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@require_http_methods(["GET"])
def current_order_items(request, table_number):
    """Return the current pending order for the Orders panel."""
    table = _get_customer_table(request, table_number)
    order = Order.objects.filter(table=table, status='pending').first()

    if not order:
        return JsonResponse({
            'items': [],
            'total_items': 0,
            'total_amount': '0.00',
        })

    items = [
        {
            'id': item.id,
            'menu_item_id': item.menu_item_id,
            'name': item.menu_item.name if item.menu_item else 'Deleted menu item',
            'quantity': item.quantity,
            'unit_price': str(item.unit_price),
            'subtotal': str(item.get_subtotal()),
        }
        for item in order.items.select_related('menu_item')
    ]

    return JsonResponse({
        'items': items,
        'total_items': sum(item['quantity'] for item in items),
        'total_amount': str(order.total_amount),
    })


@csrf_exempt
@require_http_methods(["POST"])
def update_order_item(request, table_number, item_id):
    """Update quantity of item in order"""
    table = _get_customer_table(request, table_number)
    
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 0))

        order = Order.objects.get(table=table, status='pending')
        order_item = OrderItem.objects.get(id=item_id, order=order)

        if quantity <= 0:
            order_item.delete()
        else:
            order_item.quantity = quantity
            order_item.save()

        # Update order total
        order.total_amount = sum(
            item.quantity * item.unit_price 
            for item in order.items.all()
        )
        order.save()

        return JsonResponse({
            'success': True,
            'total_amount': str(order.total_amount),
            'item_count': order.items.count(),
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@handle_access_denied
def view_cart(request, table_number):
    """View shopping cart"""
    table = _get_customer_table(request, table_number)
    
    try:
        order = Order.objects.get(table=table, status='pending')
    except Order.DoesNotExist:
        order = None

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/cart.html', context)


@handle_access_denied
def checkout(request, table_number):
    """Confirm the pending order and show a simple status handoff."""
    table = _get_customer_table(request, table_number)

    order = Order.objects.filter(table=table, status='pending').first()
    if order and order.items.exists():
        order.status = 'confirmed'
        order.save(update_fields=['status', 'updated_at'])
    else:
        order = Order.objects.filter(
            table=table,
            status__in=['confirmed', 'preparing', 'ready'],
        ).order_by('-created_at').first()

    if not order:
        return redirect('table_menu', table_number=table_number)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/checkout_modern.html', context)


@csrf_exempt
@handle_access_denied
@require_http_methods(["POST"])
def remove_from_cart(request, table_number, item_id):
    """Cancel an item in the current pending order."""
    table = _get_customer_table(request, table_number)
    
    try:
        order = Order.objects.get(table=table, status='pending')
        order_item = OrderItem.objects.get(id=item_id, order=order)
        order_item.delete()

        # Update order total
        order.total_amount = sum(
            item.quantity * item.unit_price 
            for item in order.items.all()
        )
        order.save()

        if order.items.count() == 0:
            order.delete()
            return JsonResponse({'success': True, 'order_deleted': True})

        return JsonResponse({
            'success': True,
            'order_deleted': False,
            'total_amount': str(order.total_amount),
        })

    except (Order.DoesNotExist, OrderItem.DoesNotExist):
        return JsonResponse(
            {'success': False, 'message': 'Order item not found'},
            status=404,
        )


@csrf_exempt
@handle_access_denied
@require_http_methods(["POST"])
def submit_order(request, table_number):
    """Submit order to kitchen"""
    table = _get_customer_table(request, table_number)
    
    try:
        order = Order.objects.get(table=table, status='pending')
        
        if order.items.count() == 0:
            return JsonResponse({'success': False, 'message': 'Cart is empty'})

        data = json.loads(request.body)
        order.special_instructions = data.get('special_instructions', '')
        order.status = 'confirmed'
        order.save()

        return JsonResponse({
            'success': True,
            'message': 'Order submitted!',
            'order_id': order.id,
            'order_number': order.order_number,
            'redirect_url': f'/table/{table_number}/order/{order.id}/'
        })

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No pending order'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@handle_access_denied
def order_status(request, table_number, order_id):
    """Check order status"""
    table = _get_customer_table(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/order_status.html', context)


@require_GET
def order_status_data(request, table_number, order_id):
    """Return the current order state for customer-side polling."""
    table = _get_customer_table(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)
    return JsonResponse({
        'status': order.status,
        'is_called': order.is_called,
    })


@handle_access_denied
def order_confirmation(request, table_number, order_id):
    """Order confirmation page - Modern responsive design"""
    table = _get_customer_table(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/order_confirmation_modern.html', context)


def receipt(request, table_number, order_id):
    """Display receipt"""
    table = _get_customer_table(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/receipt.html', context)


# ==================== ADMIN/CASHIER VIEWS ====================

@login_required
def dashboard(request):
    """Cashier/Admin dashboard"""
    if not request.user.is_staff:
        return redirect('index')

    # Get statistics
    pending_orders = Order.objects.filter(status__in=['pending', 'confirmed']).count()
    preparing_orders = Order.objects.filter(status='preparing').count()
    today_completed = Order.objects.filter(
        status='completed',
        completed_at__date=timezone.now().date()
    ).count()
    today_revenue = Order.objects.filter(
        status='completed',
        completed_at__date=timezone.now().date()
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    active_orders = Order.objects.filter(
        status__in=['pending', 'confirmed', 'preparing']
    ).order_by('-created_at')[:10]

    context = {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'today_completed': today_completed,
        'today_revenue': today_revenue,
        'active_orders': active_orders,
    }
    return render(request, 'menu/dashboard.html', context)


@login_required
def all_orders(request):
    """View all orders"""
    if not request.user.is_staff:
        return redirect('index')

    status_filter = request.GET.get('status', '')
    
    if status_filter:
        orders = Order.objects.filter(status=status_filter).order_by('-created_at')
    else:
        orders = Order.objects.all().order_by('-created_at')

    context = {
        'orders': orders,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'selected_status': status_filter,
    }
    return render(request, 'menu/all_orders.html', context)


@login_required
@require_http_methods(["POST"])
def update_order_status(request, order_id):
    """Update order status"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        order = Order.objects.get(id=order_id)
        data = json.loads(request.body)
        new_status = data.get('status')

        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = new_status
            if new_status == 'completed':
                order.completed_at = timezone.now()
            order.save()
            return JsonResponse({'success': True, 'message': 'Order updated'})
        
        return JsonResponse({'success': False, 'message': 'Invalid status'})

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def call_customer(request, order_id):
    """Call customer to pick up ready order"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    try:
        order = Order.objects.get(id=order_id, status='ready')
        
        # Mark as called
        order.is_called = True
        order.called_at = timezone.now()
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Customer at Table {order.table.number} called!',
            'called_at': order.called_at.strftime('%I:%M %p')
        })

    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found or not ready'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def menu_management(request):
    """Manage menu items"""
    if not request.user.is_staff:
        return redirect('index')

    categories = Category.objects.prefetch_related('items')
    
    context = {
        'categories': categories,
    }
    return render(request, 'menu/menu_management.html', context)


@login_required
def reports(request):
    """Sales and performance reports"""
    if not request.user.is_staff:
        return redirect('index')

    today = timezone.now().date()
    
    daily_revenue = Order.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    daily_orders = Order.objects.filter(
        status='completed',
        completed_at__date=today
    ).count()

    popular_items = OrderItem.objects.filter(
        order__status='completed',
        order__completed_at__date=today
    ).values('menu_item__name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    context = {
        'daily_revenue': daily_revenue,
        'daily_orders': daily_orders,
        'popular_items': popular_items,
    }
    return render(request, 'menu/reports.html', context)


# ============= STAFF LOGIN & MANAGEMENT =============

def staff_login(request):
    """Staff member login page"""
    from django.contrib.auth import authenticate, login
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('staff_panel')
        else:
            context = {'error': 'Invalid credentials or not a staff member'}
            return render(request, 'menu/staff_login.html', context)
    
    return render(request, 'menu/staff_login.html')


def staff_logout(request):
    """Staff member logout"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('staff_login')


@login_required(login_url='staff_login')
def staff_panel(request):
    """Main staff panel for managing orders"""
    if not request.user.is_staff:
        return redirect('staff_login')
    
    # Get all active orders (confirmed = pending for kitchen staff)
    pending_orders = Order.objects.filter(status='confirmed').order_by('-created_at')
    preparing_orders = Order.objects.filter(status='preparing').order_by('-created_at')
    ready_orders = Order.objects.filter(status='ready').order_by('-created_at')
    completed_orders = Order.objects.filter(status='completed').order_by('-created_at')[:10]
    
    # Calculate stats
    today = timezone.now().date()
    daily_revenue = Order.objects.filter(
        status='completed',
        completed_at__date=today
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    daily_orders_count = Order.objects.filter(
        status='completed',
        completed_at__date=today
    ).count()
    
    context = {
        'pending_orders': pending_orders,
        'preparing_orders': preparing_orders,
        'ready_orders': ready_orders,
        'completed_orders': completed_orders,
        'daily_revenue': daily_revenue,
        'daily_orders_count': daily_orders_count,
        'total_pending': pending_orders.count(),
        'total_preparing': preparing_orders.count(),
        'total_ready': ready_orders.count(),
        'staff_marquee': MarqueeSettings.load().staff_message,
    }
    return render(request, 'menu/staff_panel.html', context)


@login_required(login_url='staff_login')
def staff_order_receipt(request, order_id):
    """Display an order receipt to authenticated staff."""
    if not request.user.is_staff:
        return redirect('staff_login')

    order = get_object_or_404(Order, id=order_id)
    return render(request, 'menu/receipt.html', {
        'table': order.table,
        'order': order,
        'staff_receipt': True,
    })


@login_required(login_url='staff_login')
@require_http_methods(["POST"])
def staff_update_status(request, order_id):
    """Staff update order status"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        order = Order.objects.get(id=order_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = new_status
            if new_status == 'completed':
                order.completed_at = timezone.now()
            order.save()
            return JsonResponse({'success': True, 'message': 'Order status updated'})
        
        return JsonResponse({'success': False, 'message': 'Invalid status'})
    
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='staff_login')
@require_http_methods(["POST"])
def staff_call_customer(request, order_id):
    """Staff call customer for ready order"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    try:
        order = Order.objects.get(id=order_id, status='ready')
        order.is_called = True
        order.called_at = timezone.now()
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Table {order.table.number} called!',
            'called_at': order.called_at.strftime('%I:%M %p')
        })
    
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found or not ready'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# ============= MANAGER STAFF MANAGEMENT =============

def manager_login(request):
    """Manager login page"""
    from django.contrib.auth import authenticate, login
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('manager_panel')
        else:
            context = {'error': 'Invalid manager credentials'}
            return render(request, 'menu/manager_login.html', context)
    
    return render(request, 'menu/manager_login.html')


def manager_logout(request):
    """Manager logout"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('manager_login')


@login_required(login_url='manager_login')
def manager_panel(request):
    """Manager panel for staff management"""
    if not request.user.is_superuser:
        return redirect('manager_login')
    
    from django.contrib.auth.models import User
    
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    
    context = {
        'staff_users': staff_users,
        'total_staff': staff_users.count(),
    }
    return render(request, 'menu/manager_panel.html', context)


@login_required(login_url='manager_login')
@require_http_methods(["POST"])
def create_staff_user(request):
    """Create a new staff user"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    from django.contrib.auth.models import User
    
    try:
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        # Validate input
        if not username or not password:
            return JsonResponse({'success': False, 'message': 'Username and password required'})
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'})
        
        # Create staff user
        staff_user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Staff user "{username}" created successfully!',
            'staff_user': {
                'id': staff_user.id,
                'username': staff_user.username,
                'name': f"{staff_user.first_name} {staff_user.last_name}",
            }
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required(login_url='manager_login')
@require_http_methods(["POST"])
def delete_staff_user(request, user_id):
    """Delete a staff user"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)
    
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(id=user_id, is_staff=True, is_superuser=False)
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Staff user "{username}" deleted successfully!'
        })
    
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Staff user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
