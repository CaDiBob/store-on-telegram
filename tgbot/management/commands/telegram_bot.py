import logging
import textwrap as tw
import re

from more_itertools import chunked
from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
)

from clients.models import Client
from ._tools import (
    add_product_to_cart,
    create_client,
    get_cart_products_info,
    get_catigories,
    get_product_detail,
    get_product_name,
    get_products,
)


(
    HANDLE_CATEGORIES,
    HANDLE_CART,
    HANDLE_DESCRIPTION,
    HANDLE_MENU,
    HANDLE_SUB_CATEGORIES,
    HANDLE_PRODUCTS,
    HANDLE_WAITING,
    START_OVER
) = range(8)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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


async def start(update, context):
    logger.info('start')
    text = 'Выберете действие:'
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('📋 Каталог', callback_data='catalog')],
            [InlineKeyboardButton('🛒Корзина', callback_data='cart')],
            [InlineKeyboardButton('🗣 FAQ', callback_data='faq')]
        ]
    )
    if context.user_data.get(START_OVER):
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=keyboard
        )

    else:
        tg_user_id = update.message.chat_id
        context.user_data['tg_user_id'] = tg_user_id
        first_name = update.message.chat.first_name
        await create_client(tg_user_id, first_name)

        await update.message.reply_text(
            tw.dedent(f'''
        <b>Здравствуйте {first_name}!</b>
        Вас приветствует "Магазин в Телеграме"
        '''),
            parse_mode=ParseMode.HTML
        )

        await update.message.reply_text(
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    context.user_data[START_OVER] = True
    return HANDLE_CATEGORIES


async def show_main_page(update, context, super_category_id):
    context.user_data['current_page'] = 0
    menu = await get_menu(
        context.user_data['current_page'],
        super_category_id
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=menu
    )


async def show_next_page(update, context, super_category_id):
    context.user_data['current_page'] += 1
    menu = await get_menu(
        context.user_data['current_page'],
        super_category_id
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=menu
    )


async def show_previos_page(update, context, super_category_id):
    context.user_data['current_page'] -= 1
    menu = await get_menu(
        context.user_data['current_page'],
        super_category_id
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=menu
    )


async def get_menu(current_page, category_id):
    categories = await get_catigories(category_id)
    categories_per_page = 4
    categories_group = list(chunked(categories, categories_per_page))
    keyboard = [
        InlineKeyboardButton(
            category.name,
            callback_data=category.id)for category in categories_group[current_page]]
    footer_buttons = []
    if current_page > 0:
        footer_buttons.insert(0, InlineKeyboardButton(
            '<<<', callback_data='prev'))
    if current_page < len(categories_group) - 1:
        footer_buttons.append(InlineKeyboardButton(
            '>>>', callback_data='next'))
    footer_buttons.append(
        InlineKeyboardButton(
            'Главное меню',
            callback_data='Главное меню'))
    return InlineKeyboardMarkup(
        build_menu(
            keyboard,
            n_cols=2,
            footer_buttons=footer_buttons)
    )


async def handle_categories(update, context):
    logger.info('handle_categories new')
    context.user_data['super_category_id'] = None
    super_category_id = context.user_data['super_category_id']
    if update.callback_query.data in ('catalog', 'Назад'):
        await show_main_page(update, context, super_category_id)

    elif update.callback_query.data == 'next':
        await show_next_page(update, context, super_category_id)

    elif update.callback_query.data == 'prev':
        await show_previos_page(update, context, super_category_id)
    return HANDLE_SUB_CATEGORIES


async def handle_sub_categories(update, context):
    logger.info('handle_sud_categories new')
    if update.callback_query.data == 'next':
        super_category_id = context.user_data['super_category_id']
        await show_next_page(update, context, super_category_id)

    elif update.callback_query.data == 'prev':
        super_category_id = context.user_data['super_category_id']
        await show_previos_page(update, context, super_category_id)

    elif re.match(r'[0-9]', update.callback_query.data):
        context.user_data['super_category_id'] = update.callback_query.data
        super_category_id = context.user_data['super_category_id']
        await show_main_page(update, context, super_category_id)

    elif update.callback_query.data == 'Назад':
        super_category_id = context.user_data['super_category_id']
        await show_main_page(update, context, super_category_id)
    return HANDLE_PRODUCTS


async def handle_products(update, context):
    logger.info('handle_products new')
    product_category = update.callback_query.data
    products_category = await get_products(product_category)
    products_num = len(products_category)
    for product in products_category:
        put_cart_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton('Добавить в корзину',
                                   callback_data=product.id)]]
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=get_product_detail(product),
            reply_markup=put_cart_button,
            parse_mode=ParseMode.HTML
        )
    keyboard = [
        [
            InlineKeyboardButton('Назад', callback_data='Назад'),
            InlineKeyboardButton('Главное меню', callback_data='Главное меню')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        text=f'Показано товаров: {products_num}',
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup
    )
    return HANDLE_DESCRIPTION


async def handle_product_detail(update, context):
    logger.info('handle_product_detail')
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('Назад', callback_data='Назад')]
        ]
    )
    product_id = update.callback_query.data
    context.user_data['product_id'] = product_id
    product_detais = await get_product_name(product_id)
    await context.bot.send_message(
        text=product_detais,
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return HANDLE_CART


async def check_quantity(update, context):

    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Назад', callback_data='Назад'),
                InlineKeyboardButton('Подтвердить', callback_data='Подтвердить')
                ]
        ]
    )
    context.user_data['quantity'] = update.message.text
    await context.bot.send_message(
        text=f'Ты ввел {update.message.text}',
        chat_id=update.effective_chat.id,
        reply_markup=reply_markup
    )
    return HANDLE_CART


async def add_cart(update, context):
    logger.info('add_cart')
    if update.callback_query.data == 'Категории':
        await show_main_page(update, context, super_category_id=None)
        return HANDLE_CATEGORIES
    elif update.callback_query.data == 'Назад':
        super_category_id = context.user_data['super_category_id']
        await show_main_page(update, context, super_category_id)
        return HANDLE_PRODUCTS
    else:
        product_to_cart = await add_product_to_cart(context)
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Категории', callback_data='Категории'),
                    InlineKeyboardButton('Корзина', callback_data='Корзина'),
                    InlineKeyboardButton('Назад', callback_data='Назад')
                    ]
            ]
        )
        await context.bot.send_message(
            text= product_to_cart,
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )


async def show_cart_info(update, context):
    products = await get_cart_products_info(context)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text=products
    )

async def handle_cart(update, context):
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Назад', callback_data='Назад'),
                InlineKeyboardButton('Оплатить', callback_data='Оплатить'),
                InlineKeyboardButton('Добавить адрес для доставки', callback_data='delivery_address')
            ]
        ]
    )
    if not 'cart' in context.user_data:
        await update.callback_query.answer('Пустая корзина')
        return
    else:
        products = await get_cart_products_info(context)
        await update.callback_query.edit_message_text(
            text=products,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return HANDLE_MENU


async def cancel(update, context):
    user = update.message.from_user
    await update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def handle_error(update, context):
    logger.error(context.error)


def bot_starting():
    tg_token = settings.TG_TOKEN
    tg_chat_id = settings.TG_CHAT_ID
    application = Application.builder().token(tg_token).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(start, pattern='Назад')
            ],
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_sub_categories, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню'),
                CallbackQueryHandler(handle_cart, pattern=r'cart'),
                CallbackQueryHandler(handle_categories),
            ],
            HANDLE_SUB_CATEGORIES: [
                CallbackQueryHandler(handle_sub_categories, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню'),
                CallbackQueryHandler(handle_categories)
            ],
            HANDLE_PRODUCTS: [
                CallbackQueryHandler(handle_products, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню'),
                CallbackQueryHandler(handle_sub_categories)
            ],
            HANDLE_DESCRIPTION: [
                CallbackQueryHandler(handle_product_detail, pattern=r'[0-9]'),
                CallbackQueryHandler(handle_sub_categories, pattern=r'Назад'),
            ],
            HANDLE_CART: [
                MessageHandler(filters.TEXT, check_quantity),
                CallbackQueryHandler(handle_sub_categories, pattern=r'Назад'),
                CallbackQueryHandler(add_cart, pattern=r'Подтвердить'),
                CallbackQueryHandler(handle_cart, pattern=r'Корзина'),
                CallbackQueryHandler(add_cart)
            ],

        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


class Command(BaseCommand):
    help = 'Telegram bot'

    def handle(self, *args, **options):
        bot_starting()
