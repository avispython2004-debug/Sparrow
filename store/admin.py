from django.contrib import admin

from .models import Category, Order, OrderItem, Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    autocomplete_fields = ['product']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    ordering = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'created_at']
    list_filter = ['category', 'available', 'created_at']
    search_fields = ['name', 'description', 'category__name']
    ordering = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock', 'available']
    list_per_page = 20
    date_hierarchy = 'created_at'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'full_name', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'full_name', 'email', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    list_editable = ['status']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'status', 'total_amount')}),
        ('Customer Info', {'fields': ('full_name', 'email', 'phone')}),
        ('Shipping Address', {'fields': ('address', 'city', 'state', 'postal_code')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'subtotal']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['subtotal']
