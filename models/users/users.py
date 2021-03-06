from models.base import BaseModel
from peewee import *
from models.items.items import Items


# Определяем модель пользователя
class Users(BaseModel):
    id = AutoField(column_name='id', primary_key=True)
    tg_id = IntegerField(column_name='tg_id')
    first_name = TextField(column_name='first_name', null=True)
    last_name = TextField(column_name='last_name', null=True)
    username = TextField(column_name='username', null=True)
    language_code = TextField(column_name='language_code', null=True)
    selected_list = IntegerField(column_name='selected_list', null=True)

    class Meta:
        table_name = 'Users'


def save_user(tg_user):
    cur_user = Users.get_or_none(Users.tg_id == tg_user.id)
    if not cur_user:
        Users.create(tg_id=tg_user.id, first_name=tg_user.first_name,
                     last_name=tg_user.last_name, username=tg_user.username,
                     language_code=tg_user.language_code)


def is_new_user(tg_user):
    cur_user = Users.get_or_none(Users.tg_id == tg_user.id)
    if cur_user is None:
        return True
    else:
        return False


def set_selected_list(tg_user, list_id):
    user = Users.get(Users.tg_id == tg_user)
    user.selected_list = list_id
    user.save()


def get_selected_list_id(tg_user):
    user = Users.get(Users.tg_id == tg_user)
    return user.selected_list


def get_selected_list(tg_user):
    item = Users.\
        select(Items).\
        join(Items, on=(Users.selected_list == Items.id), attr='list').\
        where(Users.tg_id == tg_user).dicts().get()

    return item
