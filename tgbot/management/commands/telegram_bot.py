import logging
import textwrap as tw

from more_itertools import chunked
from django.conf import settings
from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from clients.models import Client
from ._tools import (
    create_client,
    get_catigories,
    get_category,
    get_products,
)


(
    HANDLE_CATEGORIES,
    HANDLE_SUB_CATEGORIES,
    HANDLE_PRODUCTS,
    START_OVER
) = range(4)


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
        * Здравствуйте {first_name}\! *
        Добро пожаловать в наш "Магазин в Телеграме"
        '''),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        await update.message.reply_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboard
        )
    context.user_data[START_OVER] = True

    return HANDLE_CATEGORIES


# async def show_next_page(update, context):
#     logger.info('show_next_page')
#     context.user_data['current_page'] += 1
#     buttons_menu = await get_buttons_menu(context.user_data['current_page'])
#     return buttons_menu
    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(
    #     text='Выберите категорию:',
    #     reply_markup=buttons_menu,
    # )


# async def show_previous_page(update, context):
#     logger.info('show_previous_page')
#     context.user_data['current_page'] -= 1
#     buttons_menu = await get_buttons_menu(context.user_data['current_page'])
#     return buttons_menu
    # await update.callback_query.answer()
    # await update.callback_query.edit_message_text(
    #     text='Выберите категорию:',
    #     reply_markup=buttons_menu,
    # )


# async def get_buttons_menu(current_page):
#     categories = await get_catigories()
#     categories_per_group = 4
#     category_groups = list(chunked(categories, categories_per_group))
#     current_page_group = category_groups[current_page]
#     keyboard = [[InlineKeyboardButton(
#         category.name, callback_data=category.id)]for category in current_page_group]
#     if current_page > 0:
#         keyboard.insert(0, [InlineKeyboardButton(
#             "<<<", callback_data="previous_page")])
#     if current_page < len(category_groups)-1:
#         keyboard.append([InlineKeyboardButton(
#             ">>>", callback_data="next_page")])
#     keyboard.append([InlineKeyboardButton(
#         "Главное меню", callback_data="Главное меню")])
#     return InlineKeyboardMarkup(keyboard)


async def get_buttons(update, context, categories, current_page):
    context.user_data['current_page'] = current_page
    if update.callback_query.data == 'next' and current_page < len(categories)-1:
        current_page += 1
        context.user_data['current_page'] = current_page
    elif update.callback_query.data == 'prev' and current_page > 0:
        current_page -= 1
        context.user_data['current_page'] = current_page

    categories_button = [
        InlineKeyboardButton(
            category.name,
            callback_data=category.id
        ) for category in categories[current_page]
    ]
    reply_markup = InlineKeyboardMarkup(
        build_menu(
            categories_button,
            n_cols=2,
            footer_buttons=get_footer_buttons(
                'prev',
                'Главное меню',
                'next'
            )
        )
    )
    return reply_markup


async def handle_categories(update, context):
    logger.info('handle_menu')
    categories = await get_catigories()
    categories_per_group = 4
    category_groups = list(chunked(categories, categories_per_group))
    if update.callback_query.data == 'catalog':
        current_page = 0
        buttons = await get_buttons(update, context, category_groups, current_page)
    else:
        current_page = context.user_data['current_page']
        buttons = await get_buttons(update, context, category_groups, current_page)
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=buttons,
    )
    return HANDLE_SUB_CATEGORIES


async def handle_sub_categories(update, context):
    logger.info('handle_categories')
    super_category_id = update.callback_query.data
    category = await get_category(super_category_id)
    categories = await get_catigories(category)
    # keyboard = [InlineKeyboardButton(
    #     category.name, callback_data=category.id) for category in categories]
    # reply_markup = InlineKeyboardMarkup(
    #     build_menu(keyboard, n_cols=2, footer_buttons=get_footer_buttons(
    #         'Главное меню', 'Корзина', 'Назад'))
    # )
    categories_per_group = 4
    category_groups = list(chunked(categories, categories_per_group))

    buttons = await get_buttons(update, context, category_groups, 0)

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=buttons
    )
    return HANDLE_PRODUCTS


async def handle_products(update, context):
    logger.info('handle_products')
    category_id = update.callback_query.data
    category_products = await get_products(category_id)
    keyboard = [
        InlineKeyboardButton(product.name, callback_data=product.id) for product in category_products
    ]
    reply_markup = InlineKeyboardMarkup(
        build_menu(keyboard, n_cols=1, footer_buttons=get_footer_buttons(
            'Назад', 'Главное меню'))
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите товар:',
        reply_markup=reply_markup
    )
    return HANDLE_PRODUCTS


async def cancel(update, context):
    user = update.message.from_user
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
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
        entry_points=[CommandHandler("start", start)],
        states={
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_categories),
                CallbackQueryHandler(start, pattern=r'Главное меню')
            ],
            HANDLE_SUB_CATEGORIES: [
                CallbackQueryHandler(handle_sub_categories, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню'),
                CallbackQueryHandler(handle_categories)
            ],
            HANDLE_PRODUCTS: [
                CallbackQueryHandler(handle_products, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню'),
                CallbackQueryHandler(handle_sub_categories),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


class Command(BaseCommand):
    help = "Telegram bot"

    def handle(self, *args, **options):
        bot_starting()
