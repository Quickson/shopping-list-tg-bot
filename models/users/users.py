from models.base import BaseModel
from peewee import *


# Определяем модель пользователя
class Users(BaseModel):
    id = AutoField(column_name='id', primary_key=True)
    tg_id = IntegerField(column_name='tg_id')
    first_name = TextField(column_name='first_name', null=True)
    last_name = TextField(column_name='last_name', null=True)
    username = TextField(column_name='username', null=True)
    language_code = TextField(column_name='language_code', null=True)

    class Meta:
        table_name = 'Users'


def save_user(tg_user):
    cur_user = Users.get_or_none(Users.tg_id == tg_user.id)
    if not cur_user:
        Users.create(tg_id=tg_user.id, first_name=tg_user.first_name,
                     last_name=tg_user.last_name, username=tg_user.username,
                     language_code=tg_user.language_code)
