"""End-to-end test of the full ecommerce flow using Django's test client.

Runs against a TEMPORARY COPY of the database so real data is never modified.
"""
import os
import re
import shutil
import tempfile

import django

# Copy the real DB to a temp file BEFORE Django starts, and point Django at the copy.
_tmp_db = os.path.join(tempfile.gettempdir(), 'sparrow_e2e_db.sqlite3')
_real_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db.sqlite3')
shutil.copy2(_real_db, _tmp_db)
os.environ['DJANGO_DATABASE_PATH'] = _tmp_db

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sparrow.settings')
os.environ.setdefault('DJANGO_DEBUG', 'True')
django.setup()

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

settings.ALLOWED_HOSTS = ['testserver']

from store.models import Category, Order, Product  # noqa: E402

PASS = '[OK]'
FAIL = '[FAIL]'
errors = []


def check(label, condition, detail=''):
    print(f'{PASS if condition else FAIL} {label} {detail}')
    if not condition:
        errors.append(label)


c = Client()

# 1. Homepage
r = c.get('/')
check('1. Homepage loads', r.status_code == 200)

# 2. Categories from DB appear
check('2. Categories shown', b'Electronics' in r.content)

# 3. Shop page
r = c.get('/shop/')
check('3. Shop loads', r.status_code == 200 and b'product-card' in r.content)

# 4. Search
r = c.get('/shop/?q=headphones')
check('4. Search finds product', b'Wireless Headphones' in r.content)
r = c.get('/shop/?q=zzzznotfound')
check('4b. Search empty state', b'No products found' in r.content)

# 5. Category filter
r = c.get('/shop/?category=electronics')
check('5. Category filter works', b'Wireless Headphones' in r.content and b'Backpack' not in r.content)

# 6. Product detail
cat = Category.objects.get(name='Electronics')
r = c.get('/product/wireless-headphones/')
check('6. Product detail', r.status_code == 200 and b'Add to Cart' in r.content)

# 7. Register
username = 'e2euser'
from django.contrib.auth.models import User as _U
_U.objects.filter(username=username).delete()
r = c.post('/register/', {'username': username, 'email': 'e2e@example.com',
                          'password1': 'Str0ngPass!99', 'password2': 'Str0ngPass!99'})
check('7. Register redirects', r.status_code == 302)

# 8. Logout then login
c.post('/logout/')
r = c.post('/login/', {'username': username, 'password': 'Str0ngPass!99'})
check('8. Login works', r.status_code == 302)

# 9. Add product to cart (POST)
p1 = Product.objects.get(name='Wireless Headphones')
stock1_before = p1.stock
r = c.post(f'/cart/add/{p1.id}/')
check('9. Add to cart', r.status_code == 302 and c.session['cart'].get(str(p1.id)) == 1)

# 10. Change quantity
r = c.post(f'/cart/update/{p1.id}/', {'quantity': 2})
check('10. Quantity updated to 2', c.session['cart'].get(str(p1.id)) == 2)

# 11. Remove a product
p2 = Product.objects.get(name='Coffee Mug')
c.post(f'/cart/add/{p2.id}/')
c.post(f'/cart/remove/{p2.id}/')
check('11. Remove product', str(p2.id) not in c.session['cart'])

# 12. Add another product
p3 = Product.objects.get(name='Backpack')
c.post(f'/cart/add/{p3.id}/')
check('12. Add second product', c.session['cart'].get(str(p3.id)) == 1)

# 13. Checkout page
r = c.get('/checkout/')
check('13. Checkout page', r.status_code == 200 and b'Order Summary' in r.content)

# 14/15. Place COD order
r = c.post('/checkout/', {'full_name': 'E2E Buyer', 'email': 'e2e@example.com', 'phone': '555-1',
                          'address': '1 Test Way', 'city': 'Town', 'state': 'TS', 'postal_code': '12345'})
check('15. Order placed -> success page', r.status_code == 302 and '/order/success/' in r.url)
m = re.search(r'/order/success/([^/]+)/', r.url)
order_number = m.group(1)

# 16. Stock decreased
p1.refresh_from_db(); p3.refresh_from_db()
check('16. Stock reduced', p1.stock == stock1_before - 2)

# 17. Cart empty
check('17. Cart cleared', c.session.get('cart') == {})

# 18. Success page
r = c.get(f'/order/success/{order_number}/')
check('18. Success page', r.status_code == 200 and order_number.encode() in r.content)

# 19. My Orders
r = c.get('/orders/')
check('19. My Orders lists order', order_number.encode() in r.content)

# 20. Order detail
r = c.get(f'/orders/{order_number}/')
check('20. Order detail', r.status_code == 200 and b'Wireless Headphones' in r.content)

# 21. Admin login (credentials come from the environment, never hardcode them)
admin_username = os.environ.get('E2E_ADMIN_USERNAME', 'admin')
admin_password = os.environ.get('E2E_ADMIN_PASSWORD', '')
admin = Client()
if admin_password:
    r = admin.post('/admin/login/', {'username': admin_username, 'password': admin_password})
    check('21. Admin login', r.status_code == 302)
else:
    print('[SKIP] 21. Admin login (set E2E_ADMIN_PASSWORD to run admin checks)')

if admin_password:
    # 22-24. Verify product, stock, order in admin
    p1.refresh_from_db()
    r = admin.get('/admin/store/product/?q=Wireless')
    check('22. Product in admin', b'Wireless Headphones' in r.content)
    r = admin.get('/admin/store/order/')
    check('24. Order in admin', order_number.encode() in r.content)
    o = Order.objects.get(order_number=order_number)
    check('23. Stock shown reduced', str(p1.stock).encode() in admin.get(f'/admin/store/product/{p1.id}/change/').content)

    # 25. Change status from admin
    r = admin.get(f'/admin/store/order/{o.id}/change/')
    items = list(o.items.all())
    post = {
        'user': o.user_id, 'full_name': o.full_name, 'email': o.email, 'phone': o.phone,
        'address': o.address, 'city': o.city, 'state': o.state, 'postal_code': o.postal_code,
        'total_amount': str(o.total_amount), 'status': 'shipped',
        'items-TOTAL_FORMS': str(len(items)), 'items-INITIAL_FORMS': str(len(items)),
        'items-MIN_NUM_FORMS': '0', 'items-MAX_NUM_FORMS': '1000',
    }
    for i, it in enumerate(items):
        post[f'items-{i}-id'] = str(it.id)
        post[f'items-{i}-product'] = str(it.product_id)
        post[f'items-{i}-quantity'] = str(it.quantity)
        post[f'items-{i}-price'] = str(it.price)
    r = admin.post(f'/admin/store/order/{o.id}/change/', post)
    if r.status_code != 302:
        html = r.content.decode('utf-8', 'ignore')
        for m in re.findall(r'<li>(.*?)</li>', html)[:10]:
            print('   errorlist:', m)
    o.refresh_from_db()
    check('25. Status changed to shipped via admin', o.status == 'shipped')

    # 26. User sees updated status
    r = c.get(f'/orders/{order_number}/')
    check('26. User sees Shipped status', b'Shipped' in r.content)
    r = c.get('/orders/')
    check('26b. Status in order list', b'Shipped' in r.content)

print()
if errors:
    print('FAILURES:', errors)
else:
    print('ALL E2E CHECKS PASSED')
