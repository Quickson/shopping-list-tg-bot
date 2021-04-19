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
from telegram import InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from models.items.items import Items, items_keyboard_markup, get_user_lists, get_items_count
from models.users.users import save_user, is_new_user, get_selected_list_id, set_selected_list, get_selected_list
from models.messages.messages import Messages
import re
from addons.admins_notifications import AdminNotification
import emoji
from telegram import KeyboardButton

HELP_TEXT = emoji.emojize('''
Бот формирует список из отправленных ему сообщений :memo:.
При нажатии на элемент списка он отмечается как выполненный :white_check_mark:.
Для удаления элемента используется кнопка :x:.
''', True)
# Это можно использовать как список покупок, дел, задач.

MAIN_KEYBOARD_MY_LIST = 'Мои списки'
MAIN_KEYBOARD_SETTINGS = 'Настройки'
MAIN_KEYBOARD_NAMES_LIST = [MAIN_KEYBOARD_MY_LIST, MAIN_KEYBOARD_SETTINGS]


FIRST, SECOND = range(2)


def user_from_update(update: Update):
    return update.effective_user


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

        text_filters = Filters.text & ~Filters.command
        text_filters = text_filters & ~Filters.text(MAIN_KEYBOARD_NAMES_LIST)
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(text_filters, self.entry_point_text_handler),
                CallbackQueryHandler(self.entry_point_callback_handler),
                CommandHandler('start', self.start_command_handler),
                CommandHandler('help', self.help_command_handler),
                MessageHandler(Filters.text(MAIN_KEYBOARD_MY_LIST), self.my_list_handler),
                MessageHandler(Filters.text(MAIN_KEYBOARD_SETTINGS), self.settings_handler)
            ],
            states={
                FIRST: [
                    MessageHandler(text_filters, self.list_text_handler),
                    MessageHandler(Filters.text(MAIN_KEYBOARD_MY_LIST), self.my_list_handler),
                    CallbackQueryHandler(self.selected_list_handler, pattern='^selectedList_'),
                ],
                SECOND: [
                    MessageHandler(text_filters, self.text_handler),
                    MessageHandler(Filters.text(MAIN_KEYBOARD_MY_LIST), self.my_list_handler),
                    CallbackQueryHandler(self.done, pattern='^done_'),
                    CallbackQueryHandler(self.remove, pattern='^remove_'),
                    CallbackQueryHandler(self.answer_list, pattern='^show_list$'),
                    CallbackQueryHandler(self.confirmation_remove_all, pattern='^confirmation_remove_all$'),
                    CallbackQueryHandler(self.remove_all, pattern='^clear_all$')
                ],
            },
            fallbacks=[CommandHandler('start', self.start_command_handler)],
        )

        # Add ConversationHandler to dispatcher that will be used for handling updates
        self.updater.dispatcher.add_handler(conv_handler)

        # log all errors
        self.updater.dispatcher.add_error_handler(error)

        self.notification.init_handlers(self.updater.dispatcher)

    def answer_list(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        selected_list = get_selected_list(user.id)
        keyboard = items_keyboard_markup(selected_list.get('id'))

        txt = 'Cписок \"{}\"'.format(selected_list.get('name'))
        if len(keyboard) == 0:
            txt += ' пуст'
        else:
            txt += ':'
        if update.message is None:
            update.callback_query.edit_message_text(
                txt,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            update.callback_query.answer()
        else:
            res_msg = update.message.reply_text(txt,
                                                reply_markup=InlineKeyboardMarkup(keyboard))
            self.clear_for_new_msg(update, res_msg)

    def clear_for_new_msg(self, update: Update, new_msg):
        msg = Messages.get_or_none(Messages.chat_id == update.message.chat_id)
        if msg:
            try:
                self.updater.bot.delete_message(msg.chat_id, msg.msg_id)
                self.updater.bot.delete_message(update.message.chat_id, update.message.message_id)
            except:
                pass
            msg.msg_id = new_msg.message_id
            msg.date = new_msg.date
            msg.save()
        else:
            Messages.create(msg_id=new_msg.message_id,
                            chat_id=new_msg.chat.id,
                            date=new_msg.date)

    def start_command_handler(self, update: Update, context: CallbackContext) -> None:
        main_menu_keyboard = []
        for b in MAIN_KEYBOARD_NAMES_LIST:
            main_menu_keyboard.append([KeyboardButton(b)])

        reply_kb_markup = ReplyKeyboardMarkup(
            main_menu_keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )

        # Send the message with menu
        self.updater.bot.send_message(
            chat_id=update.message.chat_id,
            text='Добро пожаловать! Для начала нужно создать список, а после этого уже можно будет добавлять значения в этот список. Пожалуйста, введите название списка.',
            reply_markup=reply_kb_markup
        )

        user = user_from_update(update)
        logging.info("users %s started the conversation.", user)
        if is_new_user(user):
            save_user(user)
            self.notification.notify('New user {}\nId = {}\n{}'.format(user.full_name, user.id, user.link))

        return FIRST

    def done(self, update: Update, context: CallbackContext) -> None:
        query = update.callback_query
        data = query.data
        data_list = data.split('_')
        logging.info("callback done: data = %s", data_list)

        item = Items.get(Items.id == int(data_list[1]))
        item.done = not item.done
        item.save()

        user = user_from_update(update)
        keyboard_list = items_keyboard_markup(get_selected_list_id(user.id))

        query.edit_message_reply_markup(
            InlineKeyboardMarkup(keyboard_list)
        )
        query.answer()

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

    def help_command_handler(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(HELP_TEXT)

    def text_handler(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        lst = re.split('[,;\n]+', update.message.text)
        items_data = []
        list_id = get_selected_list_id(user.id)
        for i in lst:
            name = i.strip()
            if not name:
                continue
            items_data.append({
                'user_tg_id': user.id,
                'name': i.strip(),
                'parent': list_id
            })
        Items.insert_many(items_data).execute()

        self.answer_list(update, context)
        return SECOND

    def list_text_handler(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
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

        self.my_list_handler(update, None)
        return FIRST

    def selected_list_handler(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        data = update.callback_query.data.split('_')
        set_selected_list(user.id, int(data[1]))
        self.answer_list(update, context)
        return SECOND

    def my_list_handler(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        set_selected_list(user.id, None)
        lsts = get_user_lists(user.id)
        keyboard = []
        for lst in lsts:
            cnt = get_items_count(lst.get('id'))
            name = lst.get('name')
            if cnt != 0:
                name += ' ({})'.format(cnt)

            list_line = [
                InlineKeyboardButton(name, callback_data='selectedList_' + str(lst.get('id')))
            ]
            keyboard.append(list_line)

        txt = 'Ваши списки:' if len(keyboard) != 0 else 'У вас нет созданных списков'
        if update.message:
            msg = update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(keyboard))
            self.clear_for_new_msg(update, msg)
        else:
            query = update.callback_query
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                reply_markup=reply_markup,
                text=txt,
            )
            query.answer()

        return FIRST

    def settings_handler(self, update: Update, context: CallbackContext):
        pass

    def entry_point_text_handler(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        selected_list = get_selected_list_id(user.id)
        if selected_list is None:
            # Значит добавляют список
            return self.list_text_handler(update, context)
        else:
            # Значит добавляют В список
            return self.text_handler(update, context)

    def entry_point_callback_handler(self, update: Update, context: CallbackContext):
        pass

    def confirmation_remove_all(self, update: Update, context: CallbackContext):
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

    def remove_all(self, update: Update, context: CallbackContext):
        user = user_from_update(update)
        selected_list = get_selected_list_id(user.id)
        items_query = Items.delete().where(Items.user_tg_id == int(user.id),
                                           (Items.parent == selected_list) | (Items.id == selected_list))
        items_query.execute()
        set_selected_list(user.id, None)
        return self.my_list_handler(update, context)

