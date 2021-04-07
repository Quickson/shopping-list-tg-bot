#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
# type: ignore[union-attr]
# This program is dedicated to the public domain under the CC0 license.

"""
Basic example for a bot that uses inline keyboards.
"""

import logging
from const import Config
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from models.items.items import Items, get_keyboard_markup_list
from models.users.users import save_user
from models.messages.messages import Messages
import re
from clear_list import remove_all, confirmation_remove_all, show_list
from addons.admins_notifications import AdminNotification
import emoji

HELP_TEXT = emoji.emojize('''
Бот формирует список из отправленных ему сообщений :memo:.
При нажатии на элемент списка он отмечается как выполненный :white_check_mark:.
Для удаления элемента используется кнопка :x:.
''', True)
# Это можно использовать как список покупок, дел, задач.


def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)


class BotBL:
    def __init__(self):
        self.updater = Updater(Config.TELEGRAM_TOKEN, use_context=True)
        self.notification = AdminNotification(self.updater.bot)

    def start(self):
        Config.init_logging()

        self.add_handlers()

        # Start the Bot
        if Config.MODE == 'webhook':
            logging.info(f"Starting webhook mode on port {Config.PORT}")
            logging.info(f"URL_WEBHOOK = {Config.WEBHOOK_URL}, APP_NAME = {Config.HEROKU_APP_NAME}")

            self.updater.start_webhook(
                listen="0.0.0.0",
                port=int(Config.PORT),
                url_path=Config.TELEGRAM_TOKEN,
                webhook_url="https://{}.herokuapp.com/{}".format(Config.HEROKU_APP_NAME,
                                                                 Config.TELEGRAM_TOKEN))

            logging.info(f"Webhook mode started on port {Config.PORT}")
        else:
            logging.info(f"Starting polling mode...")
            self.updater.start_polling()
            logging.info(f"Polling mode started")

        self.updater.idle()

    def add_handlers(self):
        self.updater.dispatcher.add_handler(CommandHandler('start', self.start_command_handler))
        self.updater.dispatcher.add_handler(CommandHandler('help', self.help_command_handler))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.text_handler))

        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.done, pattern='^done_'))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.remove, pattern='^remove_'))

        self.updater.dispatcher.add_handler(CallbackQueryHandler(show_list, pattern='^show_list$'))
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(confirmation_remove_all, pattern='^confirmation_remove_all$'))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(remove_all, pattern='^clear_all$'))

        # log all errors
        self.updater.dispatcher.add_error_handler(error)

        self.notification.init_handlers(self.updater.dispatcher)

    def answer_list(self, update):
        user = update.message.from_user
        keyboard = get_keyboard_markup_list(user)
        res_msg = update.message.reply_text('Ваш список:', reply_markup=InlineKeyboardMarkup(keyboard))

        msg = Messages.get_or_none(Messages.chat_id == update.message.chat_id)
        if msg:
            try:
                self.updater.bot.delete_message(msg.chat_id, msg.msg_id)
                self.updater.bot.delete_message(update.message.chat_id, update.message.message_id)
            except:
                pass
            msg.msg_id = res_msg.message_id
            msg.date = res_msg.date
            msg.save()
        else:
            Messages.create(msg_id=res_msg.message_id,
                            chat_id=res_msg.chat.id,
                            date=res_msg.date)

    def start_command_handler(self, update: Update, context: CallbackContext) -> None:
        user = update.message.from_user
        logging.info("users %s started the conversation.", user)
        save_user(user)

        self.answer_list(update)

    @staticmethod
    def done(self, update: Update, context: CallbackContext) -> None:
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

    @staticmethod
    def remove(self, update: Update, context: CallbackContext) -> None:
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

    @staticmethod
    def help_command_handler(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(HELP_TEXT)

    def text_handler(self, update: Update, context: CallbackContext):
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

        self.answer_list(update)
