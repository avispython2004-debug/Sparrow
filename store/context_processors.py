def cart_count(request):
    cart = request.session.get('cart', {})
    try:
        count = sum(int(qty) for qty in cart.values())
    except (TypeError, ValueError):
        count = 0
    return {'cart_count': count}
