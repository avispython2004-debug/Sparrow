from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Product


def _get_cart(request):
    return request.session.setdefault('cart', {})


def _save_cart(request):
    request.session.modified = True


def _cart_items(request):
    """Return (items, total); drops products that no longer exist."""
    cart = _get_cart(request)
    items = []
    total = Decimal('0.00')
    stale_ids = []

    for product_id, qty in cart.items():
        try:
            product = Product.objects.select_related('category').get(id=product_id)
        except (Product.DoesNotExist, ValueError):
            stale_ids.append(product_id)
            continue
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            qty = 0
        if qty < 1:
            stale_ids.append(product_id)
            continue
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

    for stale_id in stale_ids:
        cart.pop(stale_id, None)
    if stale_ids:
        _save_cart(request)
        messages.warning(request, 'Some products were removed from your cart because they are no longer available.')

    return items, total


def cart_detail(request):
    items, total = _cart_items(request)
    return render(request, 'cart/cart.html', {'items': items, 'total': total})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.available or product.stock < 1:
        messages.error(request, f'"{product.name}" is currently unavailable.')
        return redirect('cart')

    cart = _get_cart(request)
    current_qty = int(cart.get(str(product.id), 0))

    if current_qty + 1 > product.stock:
        messages.error(request, f'Only {product.stock} of "{product.name}" in stock.')
        return redirect('cart')

    cart[str(product.id)] = current_qty + 1
    _save_cart(request)
    messages.success(request, f'"{product.name}" added to your cart.')
    return redirect('cart')


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)

    try:
        quantity = int(request.POST.get('quantity', 0))
    except (TypeError, ValueError):
        messages.error(request, 'Invalid quantity.')
        return redirect('cart')

    if quantity < 1:
        cart.pop(str(product.id), None)
        _save_cart(request)
        messages.info(request, f'"{product.name}" removed from your cart.')
        return redirect('cart')

    if not product.available:
        messages.error(request, f'"{product.name}" is currently unavailable.')
        return redirect('cart')

    if quantity > product.stock:
        messages.error(request, f'Only {product.stock} of "{product.name}" in stock. Quantity not updated.')
        return redirect('cart')

    cart[str(product.id)] = quantity
    _save_cart(request)
    messages.success(request, f'Quantity updated for "{product.name}".')
    return redirect('cart')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_cart(request)
    if str(product.id) in cart:
        cart.pop(str(product.id))
        _save_cart(request)
        messages.info(request, f'"{product.name}" removed from your cart.')
    return redirect('cart')
