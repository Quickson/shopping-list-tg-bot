from models.base import db
from models.users.users import Users
from models.items.items import Items
from models.messages.messages import Messages

MODELS = [Users, Items, Messages]


def create_tables():
    with db:
        db.create_tables(MODELS)


def get_tables():
    res = {}
    for i in MODELS:
        res.update({i._meta.table_name.lower(): i})
    return res


def convert_tables():
    pass
