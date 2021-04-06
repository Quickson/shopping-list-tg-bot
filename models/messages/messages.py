from models.base import BaseModel
from peewee import *


# Определяем модель пользователя
class Messages(BaseModel):
    id = AutoField(column_name='id', primary_key=True)
    msg_id = IntegerField(column_name='msg_id')
    chat_id = IntegerField(column_name='chat_id')
    date = TimestampField(column_name='date')

    class Meta:
        table_name = 'Messages'





