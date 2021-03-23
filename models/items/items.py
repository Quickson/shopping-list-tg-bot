from models.base import BaseModel
from peewee import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
REMOVE_EMOJI = '\u274C'
DONE_EMOJI = '\u2705'

# Определяем модель предметы
class Items(BaseModel):
    id = AutoField(column_name='id', primary_key=True)
    user_tg_id = IntegerField(column_name='user_tg_id')
    name = TextField(column_name='name', null=False)
    done = BooleanField(column_name='done', null=False, default=False)
    num = IntegerField(column_name='num', sequence='item_por_num',
                       null=False, unique=False)

    class Meta:
        table_name = 'Items'


def get_keyboard_markup_list(user):
    query = Items.select().where(Items.user_tg_id == user.id).order_by(Items.num.asc())
    keyboard = []
    for item in query.dicts().execute():
        item_val_name = '{} {}'.format(DONE_EMOJI, item.get('name')) if item.get('done') else item.get('name')
        item_line = [
            InlineKeyboardButton(item_val_name, callback_data='done_'+str(item.get('id'))),
            InlineKeyboardButton(REMOVE_EMOJI, callback_data='remove_' + str(item.get('id'))),
        ]
        keyboard.append(item_line)

    if len(keyboard) > 0:
        keyboard.append([InlineKeyboardButton('Очистить список', callback_data='confirmation_remove_all')])
    return keyboard
