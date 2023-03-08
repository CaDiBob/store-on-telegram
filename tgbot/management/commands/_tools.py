import textwrap as tw

from django.conf import settings
import xlsxwriter
from asgiref.sync import sync_to_async
from telegram import InlineKeyboardButton

from clients.models import Client
from products.models import (
    Category,
    Product,
    Order,
    OrderItem
)
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


@sync_to_async
def remove_product_from_cart(context):
    product_id = context.user_data['product_id']
    product = Product.objects.get(id=product_id)
    cart = Cart(context)
    cart.remove(product)


def get_cart_info(context):
    cart = Cart(context)
    return cart


@sync_to_async
def get_cart_products_info(context):
    cart = Cart(context)
    products = []
    products_info = ''
    for position, product in enumerate(cart, start=1):
        products.append(product['product'])
        raw_name = product['product']
        name = raw_name.name
        quantity = product['quantity']
        price = product['price']
        product_total_price = product['total_price']
        products_info += tw.dedent(f'''
        №{position}. <b>{name}</b>
        <i>Цена:</i> ₽{price}
        <i>Количество:</i> {quantity} шт.
        <i>Стоимость:</i> ₽{product_total_price}
        ''')
    products_info += tw.dedent(f'''
    <i>Общая стоимость:</i> ₽{cart.get_total_price()}
    ''')
    return products_info, products


@sync_to_async
def get_product_info_for_payment(context):
    products_in_cart = get_cart_info(context)
    total_order_price = products_in_cart.get_total_price()
    products_info = ''
    for product in products_in_cart:
        raw_name = product['product']
        name = raw_name.name
        quantity = product['quantity']
        products_info += tw.dedent(f'''
        {name}
        Количество: {quantity} шт.
        ''')
    products_info += tw.dedent(f'''
    Общая стоимость: ₽{total_order_price}
    ''')
    return {
        'products_info': products_info,
        'total_order_price': total_order_price
    }


@sync_to_async
def create_order(context):
    cart = Cart(context)
    address = context.user_data['address']
    tg_user_id = context.user_data['tg_user_id']
    client = Client.objects.get(tg_user_id=tg_user_id)
    order = Order.objects.create(
        client=client,
        address=address,
    )
    order_elements = []
    for order_product in cart:
        product = order_product['product']
        quantity = order_product['quantity']
        order_element = OrderItem(
            order=order,
            product=product,
            quantity=quantity,
        )
        order_elements.append(order_element)
    OrderItem.objects.bulk_create(order_elements)

    return True


@sync_to_async
def get_client_orders(context):
    pass


@sync_to_async
def upload_to_exel():
    orders = Order.objects.select_related('client')
    filepath = settings.ORDERS_FILE_PATH
    workbook = xlsxwriter.Workbook(filepath)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({'bold': True})

    expenses = [
        [order.client.tg_user_id,
         order.created_at.strftime('%m/%d/%Y'),
         order.address]for order in orders]

    for row_num, row_data in enumerate(expenses):
        worksheet.write_row(row_num, 0, row_data)
    workbook.close()


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):

    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def get_footer_buttons(*args):
    footer_buttons = [
        InlineKeyboardButton(button, callback_data=button) for button in args
    ]
    return footer_buttons
