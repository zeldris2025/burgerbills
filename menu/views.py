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
from django.db.models import F, Q, Sum, Count, Prefetch
from decimal import Decimal
import csv
import json
from datetime import datetime
from urllib.parse import urlencode

from .models import Category, MarqueeSettings, MenuItem, Table, Order, OrderItem


class AccessDeniedException(Exception):
    """Custom exception for menu access denial.

    `reason` lets callers distinguish why access was refused:
        'no_table'   - table does not exist / inactive
        'invalid'    - QR token did not match
        'no_session' - never scanned, or scanned a different table
        'expired'    - session passed its hard timeout
        'completed'  - order already submitted on this session
    """

    def __init__(self, message, reason='no_session'):
        super().__init__(message)
        self.reason = reason


def _no_store(response):
    """Stop the browser caching a customer page.

    Without this the back button can redisplay the menu from cache after the order
    was placed or the session expired, instead of asking the server and landing on
    the access denied page.
    """
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def handle_access_denied(view_func):
    """Decorator to handle AccessDeniedException and display access denied page or JSON error"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except AccessDeniedException as e:
            error_msg = str(e)

            # Check if this is an AJAX/JSON request
            is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
                      request.method in ['POST', 'PUT', 'DELETE'] or
                      request.headers.get('Content-Type') == 'application/json')

            if is_ajax:
                response = JsonResponse({
                    'success': False,
                    'error': error_msg,
                    'message': error_msg
                }, status=403)
            else:
                response = render(request, 'menu/access_denied.html', {
                    'error_message': error_msg,
                }, status=403)
            return _no_store(response)
    return wrapper


def index(request):
    """Show the public Burger Bills website without ordering entry points."""
    return render(request, 'menu/index.html')


def about(request):
    """Public 'About' page reached from the hero orbit menu."""
    return render(request, 'menu/about.html', {'active_page': 'about'})


# Where Burger Bills is. Replace these four values with the real ones and every
# map, pin and directions link on the Location page follows automatically.
RESTAURANT_LOCATION = {
    'name': 'Burger Bills',
    'address': 'Apia, Samoa',
    'latitude': -13.821367013852514,
    'longitude': -171.80282614658333,
    
}


def location(request):
    """Public 'Location' page with the map and directions to the restaurant.

    The embedded map is OpenStreetMap: it frames without an API key, unlike the
    keyless Google Maps embed, which now answers with X-Frame-Options: SAMEORIGIN
    and renders as an empty box. The directions buttons still hand off to Google
    and Apple Maps, which is where people actually want to navigate from.
    """
    lat = RESTAURANT_LOCATION['latitude']
    lng = RESTAURANT_LOCATION['longitude']
    span = 0.006  # roughly 650m of map on each side of the pin

    return render(request, 'menu/location.html', {
        'active_page': 'location',
        'place': RESTAURANT_LOCATION,
        'map_embed_url': (
            'https://www.openstreetmap.org/export/embed.html'
            f'?bbox={round(lng - span, 6)}%2C{round(lat - span, 6)}'
            f'%2C{round(lng + span, 6)}%2C{round(lat + span, 6)}'
            f'&layer=mapnik&marker={lat}%2C{lng}'
        ),
        'map_google_url': f'https://www.google.com/maps/dir/?api=1&destination={lat},{lng}',
        'map_apple_url': f'https://maps.apple.com/?daddr={lat},{lng}',
        'map_osm_url': f'https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=17/{lat}/{lng}',
    })


def how_to_order(request):
    """Public 'Order' page explaining how dine-in ordering works."""
    return render(request, 'menu/how_to_order.html', {'active_page': 'order'})


def _start_qr_session(request, table):
    """Begin a fresh menu session for a customer who just scanned the table QR code."""
    request.session['qr_table_number'] = table.number
    request.session['qr_session_start_time'] = timezone.now().isoformat()
    request.session['qr_access_timeout_minutes'] = table.menu_access_timeout_minutes
    request.session['qr_order_completed'] = False
    request.session.set_expiry(table.menu_access_timeout_minutes * 60)


def _get_customer_table(request, table_number):
    """Resolve the table for a customer request, enforcing QR access rules.

    A valid ?access token always starts a brand-new session. `table_menu` strips the
    token from the URL immediately afterwards, so the one-hour clock is only ever set
    by a genuine scan and never restarts on a page refresh.
    """
    from datetime import timedelta

    try:
        table = get_object_or_404(Table, number=table_number, is_active=True)
    except Http404:
        raise AccessDeniedException(
            'Table not found. Please scan the QR code at your table.', reason='no_table'
        )

    supplied_token = request.GET.get('access')

    # A supplied token is a fresh scan of the physical QR code at the table.
    if supplied_token:
        if supplied_token != str(table.qr_access_token):
            raise AccessDeniedException(
                'Invalid QR code. Please scan the QR code at your table.', reason='invalid'
            )
        _start_qr_session(request, table)
        return table

    # No token: the customer must already hold a session for this table.
    if request.session.get('qr_table_number') != table.number:
        raise AccessDeniedException(
            'Access denied. Please scan the QR code at your table to access the menu.',
            reason='no_session',
        )

    # Hard timeout measured from the scan, never extended by activity.
    session_start_str = request.session.get('qr_session_start_time')
    timeout_minutes = request.session.get(
        'qr_access_timeout_minutes', table.menu_access_timeout_minutes
    )

    if session_start_str:
        from datetime import datetime as dt

        session_start = dt.fromisoformat(session_start_str)
        if timezone.now() > session_start + timedelta(minutes=timeout_minutes):
            raise AccessDeniedException(
                'Your menu access has expired. Please scan the QR code at your table again.',
                reason='expired',
            )

    # One order per scan - ordering again requires a new scan.
    if request.session.get('qr_order_completed', False):
        raise AccessDeniedException(
            'Your order has been placed. Please scan the QR code again to start a new order.',
            reason='completed',
        )

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

    # Drop the ?access token from the address bar once the session exists, so a
    # refresh cannot restart the one-hour clock. A new hour needs a new scan.
    if request.GET.get('access'):
        return redirect('table_menu', table_number=table.number)


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
    return _no_store(render(request, 'menu/customer_menu_fresh.html', context))


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
            # The cart needs this to remove the row or change its quantity later.
            'order_item_id': order_item.id,
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
        unit_price = data.get('unit_price')  # Price of the size variant

        # Get the pending order
        order = Order.objects.filter(table=table, status='pending').first()
        if not order:
            return JsonResponse({'success': False, 'message': 'No pending order'}, status=404)

        # Find and update the order item (filter by price if provided to distinguish size variants)
        query = order.items.filter(menu_item_id=menu_item_id)
        if unit_price is not None:
            try:
                unit_price = Decimal(str(unit_price))
                query = query.filter(unit_price=unit_price)
            except (ValueError, TypeError):
                pass

        order_item = query.first()
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
@handle_access_denied
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

        # Mark session as order completed - prevents further menu access
        # Customer must rescan QR code to place another order
        request.session['qr_order_completed'] = True

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


def _get_table_for_placed_order(request, table_number):
    """Resolve the table for a view of an order that has already been placed.

    Once an order exists the customer must still be able to watch it, print the
    receipt and refresh the page after their menu session ends - so these views
    do not require a live QR session.
    """
    try:
        return _get_customer_table(request, table_number)
    except AccessDeniedException:
        return get_object_or_404(Table, number=table_number, is_active=True)


@handle_access_denied
def order_status(request, table_number, order_id):
    """Check order status - accessible even after the menu session ends"""
    table = _get_table_for_placed_order(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/order_status.html', context)


@require_GET
def order_status_data(request, table_number, order_id):
    """Return the current order state for the customer-side 5 second poll."""
    table = _get_table_for_placed_order(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)
    return JsonResponse({
        'status': order.status,
        'is_called': order.is_called,
    })


@handle_access_denied
def order_confirmation(request, table_number, order_id):
    """Order confirmation page - accessible even after the menu session ends"""
    table = _get_table_for_placed_order(request, table_number)
    order = get_object_or_404(Order, id=order_id, table=table)

    context = {
        'table': table,
        'order': order,
    }
    return render(request, 'menu/order_confirmation_modern.html', context)


def receipt(request, table_number, order_id):
    """Display receipt - accessible even after the menu session ends"""
    table = _get_table_for_placed_order(request, table_number)
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


def _orders_for_status(status_filter):
    """Orders for the all-orders table, newest first.

    The item count is annotated rather than counted per row in the template: the
    table is polled every few seconds, so one query beats one-per-order.
    """
    orders = Order.objects.select_related('table').annotate(item_count=Count('items'))
    if status_filter:
        orders = orders.filter(status=status_filter)
    return orders.order_by('-created_at')


@login_required
def all_orders(request):
    """View all orders"""
    if not request.user.is_staff:
        return redirect('index')

    status_filter = request.GET.get('status', '')

    context = {
        'orders': _orders_for_status(status_filter),
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'selected_status': status_filter,
    }
    return render(request, 'menu/all_orders.html', context)


@require_GET
def all_orders_table(request):
    """Return just the orders table, for the auto-refresh poll on /orders/.

    Answers 403 rather than redirecting when the staff session has gone, so the
    page can stop polling instead of quietly pasting a login form into the table.
    """
    if not request.user.is_staff:
        return HttpResponse('Forbidden', status=403)

    html = render(request, 'menu/_orders_table.html', {
        'orders': _orders_for_status(request.GET.get('status', '')),
    })
    return _no_store(html)


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


def _active_order_signature():
    """Fingerprint of the live order board, shared by the panel and its poller.

    Any arrival, status change or completion moves it and nothing else does, so
    the staff panel can hold still instead of reloading on a blind timer.
    """
    active = Order.objects.filter(
        status__in=['confirmed', 'preparing', 'ready']
    ).order_by('id').values_list('id', 'status')
    return '|'.join(f'{order_id}:{status}' for order_id, status in active)


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
        'order_signature': _active_order_signature(),
    }
    return render(request, 'menu/staff_panel.html', context)


@login_required(login_url='staff_login')
@require_GET
def staff_new_orders(request):
    """Feed the staff panel the orders that are waiting to be picked up.

    The panel polls this so it can raise the new-order alarm the moment a
    customer submits, and only reload the page when the board actually changed.
    """
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    new_orders = [
        {
            'id': order.id,
            'order_number': order.order_number,
            'table': order.table.number if order.table else None,
            'total': str(order.total_amount),
            'created_at': order.created_at.isoformat(),
        }
        for order in Order.objects.filter(status='confirmed').select_related('table').order_by('-created_at')
    ]

    return JsonResponse({
        'success': True,
        'new_orders': new_orders,
        'signature': _active_order_signature(),
    })


# Orders still in 'pending' are open carts that were never sent to the kitchen,
# so every report leaves them out.
REPORT_STATUSES = ['confirmed', 'preparing', 'ready', 'completed', 'cancelled']


def _report_range(request):
    """Read the ?start=&end= dates (YYYY-MM-DD), defaulting to today.

    Returns (start, end) as dates, swapped if given the wrong way round.
    """
    today = timezone.localdate()

    def parse(value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return None

    start = parse(request.GET.get('start')) or today
    end = parse(request.GET.get('end')) or start
    if start > end:
        start, end = end, start
    return start, end


def _report_orders(request):
    """Orders placed in the requested range, optionally narrowed to one status."""
    start, end = _report_range(request)
    orders = Order.objects.filter(
        status__in=REPORT_STATUSES,
        created_at__date__gte=start,
        created_at__date__lte=end,
    )
    status = request.GET.get('status')
    if status in REPORT_STATUSES:
        orders = orders.filter(status=status)
    else:
        status = ''
    return orders, start, end, status


def _csv_safe(value):
    """Stop spreadsheet apps running customer-typed text as a formula."""
    text = '' if value is None else str(value)
    if text[:1] in ('=', '+', '-', '@', '\t', '\r'):
        return "'" + text
    return text


@login_required(login_url='staff_login')
def staff_reports(request):
    """Sales report for a date range, with CSV exports."""
    if not request.user.is_staff:
        return redirect('staff_login')

    orders, start, end, status = _report_orders(request)
    completed = orders.filter(status='completed')

    revenue = completed.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    completed_count = completed.count()

    top_items = OrderItem.objects.filter(order__in=completed).values(
        'menu_item__name'
    ).annotate(
        qty=Sum('quantity'),
        revenue=Sum(F('quantity') * F('unit_price')),
    ).order_by('-qty', 'menu_item__name')[:10]

    hourly = {}
    for created_at, amount in completed.values_list('created_at', 'total_amount'):
        hour = timezone.localtime(created_at).hour
        count, total = hourly.get(hour, (0, Decimal('0')))
        hourly[hour] = (count + 1, total + amount)
    best_hour_revenue = max((total for _, total in hourly.values()), default=Decimal('0'))
    hourly_rows = [
        {
            'label': f'{hour:02d}:00',
            'orders': count,
            'revenue': total,
            'percent': int(total / best_hour_revenue * 100) if best_hour_revenue else 0,
        }
        for hour, (count, total) in sorted(hourly.items())
    ]

    type_labels = dict(Order.ORDER_TYPE_CHOICES)
    by_type = [
        {'label': type_labels.get(row['order_type'], row['order_type']), **row}
        for row in completed.values('order_type').annotate(
            orders=Count('id'), revenue=Sum('total_amount')
        ).order_by('-revenue')
    ]

    query = {'start': start.isoformat(), 'end': end.isoformat()}
    if status:
        query['status'] = status

    context = {
        'start': start,
        'end': end,
        'status': status,
        'status_choices': [c for c in Order.ORDER_STATUS_CHOICES if c[0] in REPORT_STATUSES],
        'total_orders': orders.count(),
        'completed_count': completed_count,
        'cancelled_count': orders.filter(status='cancelled').count(),
        'revenue': revenue,
        'average_order': (revenue / completed_count) if completed_count else Decimal('0'),
        'items_sold': OrderItem.objects.filter(order__in=completed).aggregate(n=Sum('quantity'))['n'] or 0,
        'top_items': top_items,
        'hourly_rows': hourly_rows,
        'by_type': by_type,
        'recent_orders': orders.select_related('table').order_by('-created_at')[:25],
        'export_query': urlencode(query),
        'staff_marquee': MarqueeSettings.load().staff_message,
    }
    return render(request, 'menu/staff_reports.html', context)


@login_required(login_url='staff_login')
@require_GET
def staff_reports_export(request):
    """Download the report range as CSV: ?kind=orders (default) or ?kind=items."""
    if not request.user.is_staff:
        return redirect('staff_login')

    orders, start, end, _ = _report_orders(request)
    orders = orders.select_related('table').order_by('created_at')
    kind = 'items' if request.GET.get('kind') == 'items' else 'orders'

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="burgerbills-{kind}-{start.isoformat()}-to-{end.isoformat()}.csv"'
    )
    # Byte-order mark so Excel opens the file as UTF-8.
    response.write('﻿')
    writer = csv.writer(response)

    def local(value):
        return timezone.localtime(value).strftime('%Y-%m-%d %H:%M') if value else ''

    if kind == 'orders':
        writer.writerow([
            'Order number', 'Placed', 'Completed', 'Status', 'Type', 'Table',
            'Customer', 'Phone', 'Items', 'Total', 'Special instructions',
        ])
        orders = orders.annotate(item_count=Sum('items__quantity'))
        for order in orders:
            writer.writerow([_csv_safe(v) for v in (
                order.order_number,
                local(order.created_at),
                local(order.completed_at),
                order.get_status_display(),
                order.get_order_type_display(),
                order.table.number if order.table else '',
                order.customer_name,
                order.customer_phone,
                order.item_count or 0,
                order.total_amount,
                order.special_instructions,
            )])
    else:
        writer.writerow([
            'Order number', 'Placed', 'Status', 'Table', 'Item', 'Quantity',
            'Unit price', 'Subtotal', 'Special requests',
        ])
        items = OrderItem.objects.filter(order__in=orders).select_related(
            'order', 'order__table', 'menu_item'
        ).order_by('order__created_at', 'created_at')
        for item in items:
            writer.writerow([_csv_safe(v) for v in (
                item.order.order_number,
                local(item.order.created_at),
                item.order.get_status_display(),
                item.order.table.number if item.order.table else '',
                item.menu_item.name if item.menu_item else 'Deleted menu item',
                item.quantity,
                item.unit_price,
                item.get_subtotal(),
                item.special_requests,
            )])

    return response


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
