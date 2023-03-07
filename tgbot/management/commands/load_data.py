from django.core.management.base import BaseCommand

from products.models import Category, Product
from ._products import products_with_price


CATEGORIES = {
    'Электроника': [
        'Смартфоны',
        'Планшеты',
        'Ноутбуки',
        'Телевизоры',
        'Смарт-часы',
        'Аудиотехника',
        'Мониторы',
        'Игровые приставки',
        'Умный дом',
        'Телефоны'
    ],
    'Бытовая техника': [
        'Холодильники',
        'Плиты',
        'Утюги',
        'Увлажнители воздуха',
        'Техника для кухни',
        'Пылесосы',
        'Напольные весы'
    ],
    'Продукты питания':[
        'Конфенты',
        'Молоко',
    ],
    'Бытовая химия': [
        'Средства для посуды',
        'Стиральные порошки',
    ],
    'Товары для животных': [
        'Корма для животных',
        'Аксесуары для животных',
    ]
}


def create_products():
    for product in products_with_price:
        category = Category.objects.get(name=product['category'])
        new_product = Product.objects.get_or_create(
            name=product['name'],
            description=product['description'],
            price=product['price'],
            category=category,
        )
        print(f'{new_product} добавлен')


def create_categories():
    for category, sub_categories in CATEGORIES.items():
        Category.objects.get_or_create(
            name=category
        )
        print(f'{category} добавлена')
        sup_cat = Category.objects.get(name=category)
        for sub_category in sub_categories:
            Category.objects.get_or_create(
                name=sub_category,
                sub_category=sup_cat
            )
            print(f'{sub_category} с надкотегорией {category} добавлена')


class Command(BaseCommand):
    help = "Load data"

    def handle(self, *args, **options):
        create_categories()
        create_products()
