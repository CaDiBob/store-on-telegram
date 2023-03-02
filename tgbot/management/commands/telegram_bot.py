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
    HANDLE_MENU,
    HANDLE_PRODUCTS,
    START_OVER
) = range(4)


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


class TelegramLogsHandler(logging.Handler):

    def __init__(self, chat_id, bot):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


async def start(update, context):

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
        tg_user_id = update.message.chat_id
        context.user_data['tg_user_id'] = tg_user_id
        first_name = update.message.chat.first_name
        await create_client(tg_user_id, first_name)

        await update.message.reply_text(
            tw.dedent(f'''
        Здравствуйте {first_name}\!
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
    return HANDLE_MENU


async def handle_menu(update, context):
    categories = await get_catigories()
    keyboard = [InlineKeyboardButton(
        category.name, callback_data=category.id) for category in categories]
    reply_markup = InlineKeyboardMarkup(
        build_menu(keyboard, n_cols=2, footer_buttons=get_footer_buttons(
            'Главное меню', 'Корзина'))
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=reply_markup
    )
    return HANDLE_CATEGORIES


async def handle_categories(update, context):
    super_category_id = update.callback_query.data
    category = await get_category(super_category_id)
    categories = await get_catigories(category)
    keyboard = [InlineKeyboardButton(
        category.name, callback_data=category.id) for category in categories]
    reply_markup = InlineKeyboardMarkup(
        build_menu(keyboard, n_cols=2, footer_buttons=get_footer_buttons(
            'Главное меню', 'Корзина', 'Назад'))
    )
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text='Выберите категорию:',
        reply_markup=reply_markup
    )
    return HANDLE_PRODUCTS


async def handle_products(update, context):
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
    logger.addHandler(TelegramLogsHandler(tg_chat_id, application.bot))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HANDLE_MENU: [
                CallbackQueryHandler(handle_menu),
                CallbackQueryHandler(start, pattern=r'Назад'),
                CallbackQueryHandler(start, pattern=r'Главное меню')
            ],
            HANDLE_CATEGORIES: [
                CallbackQueryHandler(handle_categories, pattern=r'[0-9]'),
                CallbackQueryHandler(handle_menu, pattern=r'Назад'),
                CallbackQueryHandler(start, pattern=r'Главное меню')
            ],
            HANDLE_PRODUCTS: [
                CallbackQueryHandler(handle_products, pattern=r'[0-9]'),
                CallbackQueryHandler(handle_categories, pattern=r'[0-9]'),
                CallbackQueryHandler(start, pattern=r'Главное меню')
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
