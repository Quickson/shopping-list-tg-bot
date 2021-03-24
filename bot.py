#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""

import logging
from const import TOKEN_ID
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from models.items.items import Items, get_keyboard_markup_list
from models.users.users import save_user
import re
import os
from clear_list import remove_all, confirmation_remove_all, show_list

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


class Config:
    PORT = int(os.environ.get("PORT", 5000))
    TELEGRAM_TOKEN = os.environ.get("TOKEN_SHOPPING_LIST", "")
    MODE = os.environ.get("MODE", "polling")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    HEROKU_APP_NAME = os.environ.get("APP_NAME", "")

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    @staticmethod
    def init_logging():
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            level=Config.LOG_LEVEL)


def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info("users %s started the conversation.", user)

    save_user(user)

    keyboard = get_keyboard_markup_list(user)
    update.message.reply_text('Ваш список:', reply_markup=InlineKeyboardMarkup(keyboard))


def done(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    data_list = data.split('_')
    logger.info("callback done: data = %s", data_list)

    item = Items.get(Items.id == int(data_list[1]))
    item.done = not item.done
    item.save()

    keyboard_list = get_keyboard_markup_list(query.from_user)

    #keyboard_list = query.message.reply_markup.inline_keyboard
    # for i in keyboard_list:
    #     if i[0].callback_data != data:
    #         continue
    #     if i[0].text.startswith(DONE_EMOJI):
    #         i[0].text = i[0].text[len(DONE_EMOJI):]
    #     else:
    #         i[0].text = DONE_EMOJI + i[0].text

    query.edit_message_reply_markup(
        InlineKeyboardMarkup(keyboard_list)
    )
    query.answer()


def remove(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')
    logger.info("callback remove: data = %s", data)

    items_query = Items.delete().where(Items.id == int(data[1]))
    items_query.execute()

    keyboard_list = query.message.reply_markup.inline_keyboard
    new_keyboard_list = [i for i in keyboard_list if len(i) <= 1 or i[1].callback_data != query.data]
    query.edit_message_reply_markup(
        InlineKeyboardMarkup(new_keyboard_list)
    )
    query.answer()


def help_command(update: Update, context: CallbackContext) -> None:
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

    # query = Items.select().where(Items.user_tg_id == user.id)
    # keyboard = []
    # for item in query.dicts().execute():
    #     item_line = [
    #         InlineKeyboardButton(item.get('name'), callback_data='done_'+str(item.get('id'))),
    #         InlineKeyboardButton(REMOVE_EMOJI, callback_data='remove_' + str(item.get('id'))),
    #     ]
    #     keyboard.append(item_line)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_markdown('Ваш список:', reply_markup=reply_markup)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def start_bot():
    Config.init_logging()
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN_ID, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(done, pattern='^done_'))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove, pattern='^remove_'))

    updater.dispatcher.add_handler(CallbackQueryHandler(show_list, pattern='^show_list$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(confirmation_remove_all, pattern='^confirmation_remove_all$'))
    updater.dispatcher.add_handler(CallbackQueryHandler(remove_all, pattern='^clear_all$'))

    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, add_to_list))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    logger.info("URL_WEBHOOK = {}".format(Config.WEBHOOK_URL))
    logger.info("PORT = {}".format(Config.PORT))
    logger.info("URL_WEBHOOK + TOKEN_ID = {}".format(Config.WEBHOOK_URL + Config.TELEGRAM_TOKEN))
    # Start the Bot
    if Config.MODE == 'webhook':

        # updater.bot.setWebhook(Config.WEBHOOK_URL + Config.TELEGRAM_TOKEN)
        # updater.start_webhook(listen="0.0.0.0",
        #                       port=int(Config.PORT),
        #                       url_path=Config.TELEGRAM_TOKEN)
        updater.start_webhook(listen="0.0.0.0",
                              port=int(Config.PORT),
                              url_path=Config.TELEGRAM_TOKEN,
                              webhook_url="https://{}.herokuapp.com/{}".format(Config.HEROKU_APP_NAME, Config.TELEGRAM_TOKEN))

        logging.info(f"Start webhook mode on port {Config.PORT}")
    else:
        updater.start_polling()
        logging.info(f"Start polling mode")
        
    # Run the bot until the users presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()
