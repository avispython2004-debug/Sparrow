import random
import re
import shutil
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from store.models import Category, Product

MEDIA_PRODUCTS = Path(settings.MEDIA_ROOT) / 'products'
STATIC_IMAGES = Path(settings.BASE_DIR) / 'static' / 'images'

CATEGORY_RULES = {
    'Electronics': ['macbook', 'laptop', 'iphone', 'asus', 'google', 'playstation', 'samsung', 'sony', 'jbl', 'headphone', 't.v', 'tv', 'spiker', 'speaker', '10 pro'],
    'Fashion': ['outfit', 'sute', 'suit', 'jaket', 'jacket', 'trendy', 'rich'],
    'Accessories': ['watch', 'mirror', 'glasses', 'hat', 'sun', 'makhar', 'travel'],
}


def guess_category(name):
    lowered = name.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return 'Home & Living'


def clean_name(filename):
    name = Path(filename).stem
    name = re.sub(r'[_-]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()


class Command(BaseCommand):
    help = 'Add images from static/images as products with random prices'

    def handle(self, *args, **options):
        MEDIA_PRODUCTS.mkdir(parents=True, exist_ok=True)

        created_count = 0
        for image_path in sorted(STATIC_IMAGES.iterdir()):
            if image_path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
                continue

            name = clean_name(image_path.name)
            category_name = guess_category(image_path.name)
            category, _ = Category.objects.get_or_create(name=category_name)

            destination = MEDIA_PRODUCTS / image_path.name
            if not destination.exists():
                shutil.copy2(image_path, destination)

            price = Decimal(random.randint(199, 49999)) / 100

            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': f'{name} available now.',
                    'price': price,
                    'stock': random.randint(5, 50),
                    'available': True,
                    'image': f'products/{image_path.name}',
                },
            )
            if created:
                created_count += 1
            self.stdout.write(('Created' if created else 'Exists ') + f' product: {name} (${price})')

        self.stdout.write(self.style.SUCCESS(f'Done. {created_count} product(s) added.'))
