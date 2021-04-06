import os
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from models.create_tables import get_tables


class AdminNotification:
    def __init__(self, bot: Bot):
        admin_chat_id = os.environ.get('ADMIN_CHAT_ID', None)
        self.admin_chat_id = int(admin_chat_id) if admin_chat_id else None
        self.bot = bot

    def init_handlers(self, dispatcher: Dispatcher):
        dispatcher.add_handler(CommandHandler('admin', self.admin_handler))
        dispatcher.add_handler(CommandHandler('count', self.count_handler))

    def admin_handler(self, update: Update, context: CallbackContext):
        if not self._is_admin(update.message.chat_id):
            return

        update.message.reply_text("""
            /count table_name    
        """)

    def count_handler(self, update: Update, context: CallbackContext):
        if not self._is_admin(update.message.chat_id):
            return

        splited = update.message.text.split()
        if len(splited) > 1:
            table_name = splited[1]
            reply_msg = 'Таблица {} не поддерживается'.format(table_name)
            tables = get_tables()
            if table_name.lower() in tables:
                reply_msg = tables[table_name.lower()].select().count()

            update.message.reply_text(reply_msg)

    def notify(self, text: str):
        if self.admin_chat_id:
            self.bot.send_message(self.admin_chat_id, text)

    def _is_admin(self, char_id):
        if self.admin_chat_id is None or char_id != self.admin_chat_id:
            return False
        return True


