from django.core.management.base import BaseCommand

from products.models import Category, Product
from ._products import products_with_price


CATEGORIES = {
    'Электроника': [
        'Смартфоны',
        'Планшеты',
        'Ноутбуки',
        'Телевизоры',
        'Смарт-часы'
    ],
    'Бытовая техника': [
        'Холодильники',
        'Плиты',
        'Утюги',
        'Увлажнители воздуха',
    ]
}


def create_products():
    for product in products_with_price:
        category = Category.objects.get(name=product['category'])
        new_product = Product(
            name=product['name'],
            description=product['description'],
            price=product['price'],
            category=category,
        )
        new_product.save()
        print(f'{new_product.name} добавлен')


def create_categories():
    for category, sub_categories in CATEGORIES.items():
        if Category.objects.get(name=category):
            continue
        new_super_category = Category.objects.get_or_create(
            name=category
        )
        print(f'{category} добавлена')
        for sub_category in sub_categories:
            new_sub_category = Category.objects.get_or_create(
                name=sub_category,
                sub_category=new_super_category
            )
            print(f'{sub_category} с надкотегорией {category} добавлена')


class Command(BaseCommand):
    help = "Load data"

    def handle(self, *args, **options):
        create_categories()
        create_products()
