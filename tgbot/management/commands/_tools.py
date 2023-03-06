import textwrap as tw

from asgiref.sync import sync_to_async

from clients.models import Client
from products.models import Category, Product
from cart.cart import Cart


@sync_to_async
def get_clients():
    clients = [client.tg_user_id for client in Client.objects.all()]
    return clients


@sync_to_async
def create_client(tg_user_id, first_name):
    client = Client.objects.get_or_create(
        tg_user_id=tg_user_id,
        first_name=first_name
    )
    return client


@sync_to_async
def get_catigories(super_category=None):
    categories = Category.objects.filter(sub_category=super_category)
    return [category for category in categories]


@sync_to_async
def get_category(category_id):
    category = Category.objects.get(id=category_id)
    return category


@sync_to_async
def get_products(category_id):
    products = Product.objects.select_related(
        'category').filter(category=category_id)
    return [product for product in products]


def get_product_detail(product):
    return tw.dedent(f'''
    <b>{product.name}</b>
    <i>{product.description}</i>
    Цена <b>{product.price}</b> руб.
    ''')


@sync_to_async
def get_product_name(product_id):
    product = Product.objects.get(id=product_id)
    return tw.dedent(f'''
    <b>{product.name}</b>
    цена <b>{product.price}</b>

    Введите количество:
    ''')


@sync_to_async
def add_product_to_cart(context):
    product_id = context.user_data['product_id']
    quantity = int(context.user_data['quantity'])
    product = Product.objects.get(id=product_id)
    cart = Cart(context)
    cart.add(product=product,
             quantity=quantity)
    return tw.dedent(f'''
    Добавлено в корзину:
    <b>{quantity} шт. {product.name}</b>''')


def remove_product_from_cart(context):
    product_id = context.user_data['product_id']
    cart = Cart(context)
    product = product = Product.objects.get(id=product_id)
    cart.remove(product)



def get_cart_info(context):
    cart = Cart(context)
    return cart


@sync_to_async
def get_cart_products_info(context):
    products_in_cart = get_cart_info(context)
    products_info = ''
    for product in products_in_cart:
        raw_name = product['product']
        name = raw_name.name
        quantity = product['quantity']
        price = product['price']
        product_total_price = product['total_price']
        products_info += tw.dedent(f'''
        <b>{name}</b>
        <i>Цена:</i> ₽{price}
        <i>Количество:</i> {quantity} шт.
        <i>Стоимость:</i> ₽{product_total_price}
        ''')
    products_info += tw.dedent(f'''
    <i>Общая стоимость:</i> ₽{products_in_cart.get_total_price()}
    ''')
    return products_info


@sync_to_async
def create_client_address(address, tg_user_id):
    client = Client.objects.get(tg_user_id=tg_user_id)
    client.address = address
    client.save()
