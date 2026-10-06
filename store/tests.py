from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Category, Order, Product


class BaseShopTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category, name='Headphones', price='79.99', stock=5, available=True,
        )
        self.user = User.objects.create_user(username='alice', password='Str0ngPass!99')


class CartTests(BaseShopTest):
    def test_add_to_cart(self):
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.assertEqual(self.client.session['cart'][str(self.product.id)], 1)

    def test_add_beyond_stock_rejected(self):
        for _ in range(5):
            self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.assertEqual(self.client.session['cart'][str(self.product.id)], 5)

    def test_update_quantity_invalid(self):
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('cart_update', args=[self.product.id]), {'quantity': 'abc'})
        self.assertEqual(self.client.session['cart'][str(self.product.id)], 1)

    def test_update_removes_when_zero(self):
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('cart_update', args=[self.product.id]), {'quantity': '0'})
        self.assertNotIn(str(self.product.id), self.client.session['cart'])


class CheckoutTests(BaseShopTest):
    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('cart_add', args=[self.product.id]))
        response = self.client.post(reverse('checkout'), {
            'full_name': 'Alice A', 'email': 'alice@example.com', 'phone': '555',
            'address': '1 Way', 'city': 'Town', 'state': 'TS', 'postal_code': '12345',
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.client.session['cart'], {})

    def test_checkout_rejects_invalid_email(self):
        self.client.force_login(self.user)
        self.client.post(reverse('cart_add', args=[self.product.id]))
        self.client.post(reverse('checkout'), {
            'full_name': 'Alice A', 'email': 'not-an-email', 'phone': '555',
            'address': '1 Way', 'city': 'Town', 'state': 'TS', 'postal_code': '12345',
        })
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)


class OrderAuthorizationTests(BaseShopTest):
    def test_cannot_view_other_users_order(self):
        order = Order.objects.create(
            user=self.user, full_name='Alice', email='a@example.com', phone='1',
            address='x', city='x', state='x', postal_code='x', total_amount='10',
        )
        other = User.objects.create_user(username='bob', password='Str0ngPass!99')
        self.client.force_login(other)
        response = self.client.get(reverse('order_detail', args=[order.order_number]))
        self.assertEqual(response.status_code, 404)
