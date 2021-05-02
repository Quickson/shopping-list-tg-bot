from models.base import BaseModel
from peewee import *


# Определяем модель предметы
class Items(BaseModel):
    id = AutoField(column_name='id', primary_key=True)
    user_tg_id = IntegerField(column_name='user_tg_id')
    name = TextField(column_name='name', null=False)
    done = BooleanField(column_name='done', null=False, default=False)
    num = IntegerField(column_name='num', sequence='item_por_num',
                       null=False, unique=False)
    parent = ForeignKeyField('self', null=True, backref='children')

    class Meta:
        table_name = 'Items'


def get_items(list_id):
    query = Items.select().where(Items.parent == list_id).order_by(Items.num.asc())
    result = [item for item in query.dicts().execute()]
    return result


def get_items_count(list_id):
    return Items.select().where(Items.parent == list_id).count()


def get_user_lists(user_id):
    query = Items.select().where(Items.user_tg_id == user_id, Items.parent.is_null(True)).order_by(Items.num.asc())
    result = [lst for lst in query.dicts().execute()]
    return result
