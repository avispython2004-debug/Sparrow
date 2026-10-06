from django.core.management.base import BaseCommand

from store.models import Category, Product

CATEGORIES = [
    ('Electronics', 'Gadgets and devices for everyday use'),
    ('Fashion', 'Clothing, shoes, and apparel'),
    ('Accessories', 'Everyday add-ons and small items'),
    ('Home & Living', 'Products for your home'),
]

PRODUCTS = [
    ('Electronics', 'Wireless Headphones', 'Comfortable over-ear headphones with noise cancellation and 30-hour battery life.', '79.99', 25),
    ('Electronics', 'Smart Watch', 'Track fitness, heart rate, and notifications with this stylish smartwatch.', '129.99', 15),
    ('Electronics', 'Mechanical Keyboard', 'Tactile mechanical keyboard with RGB backlighting, perfect for gaming and typing.', '89.99', 20),
    ('Accessories', 'Laptop Stand', 'Adjustable aluminum laptop stand for better posture and airflow.', '34.99', 40),
    ('Fashion', 'Backpack', 'Durable everyday backpack with padded laptop compartment.', '49.99', 30),
    ('Fashion', 'Sneakers', 'Lightweight breathable sneakers for all-day comfort.', '59.99', 50),
    ('Accessories', 'Smartphone Case', 'Shockproof slim case with raised edges for screen protection.', '14.99', 100),
    ('Home & Living', 'Coffee Mug', 'Ceramic 350ml coffee mug, microwave and dishwasher safe.', '12.99', 60),
]


class Command(BaseCommand):
    help = 'Seed the database with sample categories and products'

    def handle(self, *args, **options):
        categories = {}
        for name, description in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': description},
            )
            categories[name] = category
            self.stdout.write(('Created' if created else 'Exists ') + f' category: {name}')

        created_count = 0
        for category_name, name, description, price, stock in PRODUCTS:
            _, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': categories[category_name],
                    'description': description,
                    'price': price,
                    'stock': stock,
                    'available': True,
                },
            )
            if created:
                created_count += 1
            self.stdout.write(('Created' if created else 'Exists ') + f' product: {name}')

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created_count} new product(s) added, {len(PRODUCTS) - created_count} already existed.'
        ))
