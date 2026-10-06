from django.urls import path

from . import cart, checkout, views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('cart/', cart.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', cart.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', cart.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', cart.cart_remove, name='cart_remove'),
    path('checkout/', checkout.checkout, name='checkout'),
    path('order/success/<str:order_number>/', checkout.order_success, name='order_success'),
    path('orders/', checkout.order_list, name='order_list'),
    path('orders/<str:order_number>/', checkout.order_detail, name='order_detail'),
]
