from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def home(request):
    featured_products = Product.objects.filter(available=True).order_by('-created_at')[:4]
    latest_products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    categories = Category.objects.all()[:6]
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
    }
    return render(request, 'home.html', context)


def product_list(request):
    products = Product.objects.select_related('category').all()

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    category_slug = request.GET.get('category', '').strip()
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    products = products.order_by('name')
    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': Category.objects.all(),
        'query': query,
        'active_category': active_category,
    }
    return render(request, 'shop/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug)
    related = Product.objects.filter(category=product.category, available=True).exclude(id=product.id)[:4]
    return render(request, 'shop/product_detail.html', {'product': product, 'related': related})
