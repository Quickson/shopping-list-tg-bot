from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from models.items.items import Items, get_keyboard_markup_list


def confirmation_remove_all(update: Update, context: CallbackContext):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("ДА! Удалить все", callback_data='clear_all')],
        [InlineKeyboardButton("НЕТ! Я передумал", callback_data='show_list')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        reply_markup=reply_markup,
        text='Вы действительно хотите удалить все элементы списка?',
    )
    query.answer()


def remove_all(update: Update, context: CallbackContext):
    user = update.callback_query.from_user
    items_query = Items.delete().where(Items.user_tg_id == int(user.id))
    items_query.execute()

    show_list(update, None)


def show_list(update: Update, context: CallbackContext):
    query = update.callback_query

    user = update.callback_query.from_user
    keyboard = get_keyboard_markup_list(user)

    txt = ' пуст' if len(keyboard) == 0 else ':'
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(
        reply_markup=reply_markup,
        text='Ваш список{}'.format(txt),
    )
    query.answer()
