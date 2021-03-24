#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""

import logging
from const import TOKEN_ID, Config
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from models.items.items import Items, get_keyboard_markup_list
from models.users.users import save_user
import re
from clear_list import remove_all, confirmation_remove_all, show_list


def start_command_handler(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logging.info("users %s started the conversation.", user)

    save_user(user)

    keyboard = get_keyboard_markup_list(user)
    update.message.reply_text('Ваш список:', reply_markup=InlineKeyboardMarkup(keyboard))


def done(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    data_list = data.split('_')
    logging.info("callback done: data = %s", data_list)

    item = Items.get(Items.id == int(data_list[1]))
    item.done = not item.done
    item.save()

    keyboard_list = get_keyboard_markup_list(query.from_user)

    query.edit_message_reply_markup(
        InlineKeyboardMarkup(keyboard_list)
    )
    query.answer()


def remove(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')
    logging.info("callback remove: data = %s", data)

    items_query = Items.delete().where(Items.id == int(data[1]))
    items_query.execute()

    keyboard_list = query.message.reply_markup.inline_keyboard
    new_keyboard_list = [i for i in keyboard_list if len(i) <= 1 or i[1].callback_data != query.data]
    query.edit_message_reply_markup(
        InlineKeyboardMarkup(new_keyboard_list)
    )
    query.answer()


def help_command_handler(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Use /start to test this bot.")


def add_to_list(update: Update, context: CallbackContext):
    user = update.message.from_user
    lst = re.split('[,;\n]+', update.message.text)
    items_data = []
    for i in lst:
        name = i.strip()
        if not name:
            continue
        items_data.append({
            'user_tg_id': user.id,
            'name': i.strip()
        })
    Items.insert_many(items_data).execute()

    keyboard = get_keyboard_markup_list(user)
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_markdown('Ваш список:', reply_markup=reply_markup)


def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def start_bot():
    Config.init_logging()

    updater = Updater(TOKEN_ID, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start_command_handler))
    updater.dispatcher.add_handler(CommandHandler('help', help_command_handler))

    updater.dispatcher.add_handler(CallbackQueryHandler(done, pattern='^done_'))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove, pattern='^remove_'))

    updater.dispatcher.add_handler(CallbackQueryHandler(show_list, pattern='^show_list$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(confirmation_remove_all, pattern='^confirmation_remove_all$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_all, pattern='^clear_all$'))

    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, add_to_list))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    if Config.MODE == 'webhook':
        logging.info(f"Starting webhook mode on port {Config.PORT}")
        logging.info(f"URL_WEBHOOK = {Config.WEBHOOK_URL}, APP_NAME = {Config.HEROKU_APP_NAME}")

        updater.start_webhook(listen="0.0.0.0",
                              port=int(Config.PORT),
                              url_path=Config.TELEGRAM_TOKEN,
                              webhook_url="https://{}.herokuapp.com/{}".format(Config.HEROKU_APP_NAME, Config.TELEGRAM_TOKEN))

        logging.info(f"Webhook mode started on port {Config.PORT}")
    else:
        logging.info(f"Starting polling mode...")
        updater.start_polling()
        logging.info(f"Polling mode started")

    updater.idle()
