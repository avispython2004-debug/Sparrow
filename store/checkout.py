from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .cart import _cart_items
from .models import Order, OrderItem, Product


@login_required
def checkout(request):
    items, total = _cart_items(request)

    if not items:
        messages.error(request, 'Your cart is empty. Add products before checking out.')
        return redirect('product_list')

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        if not all([full_name, email, phone, address, city, state, postal_code]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'orders/checkout.html', {'items': items, 'total': total})

        try:
            EmailValidator()(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'orders/checkout.html', {'items': items, 'total': total})

        try:
            with transaction.atomic():
                # Re-validate availability and stock inside the transaction
                for item in items:
                    product = Product.objects.select_for_update().get(id=item['product'].id)
                    if not product.available:
                        raise ValueError(f'"{product.name}" is no longer available.')
                    if item['quantity'] > product.stock:
                        raise ValueError(f'Not enough stock for "{product.name}" ({product.stock} left).')

                order_total = sum(item['subtotal'] for item in items)
                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    postal_code=postal_code,
                    total_amount=order_total,
                    status='pending',
                )

                for item in items:
                    product = Product.objects.get(id=item['product'].id)
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=product.price,
                    )
                    product.stock -= item['quantity']
                    if product.stock < 0:
                        raise ValueError(f'Not enough stock for "{product.name}".')
                    product.save()

            request.session['cart'] = {}
            request.session.modified = True
            messages.success(request, 'Order placed successfully!')
            return redirect('order_success', order_number=order.order_number)

        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('cart')

    return render(request, 'orders/checkout.html', {'items': items, 'total': total})


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})
