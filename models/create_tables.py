from models.base import db
from models.users.users import Users
from models.items.items import Items


def create_tables():
    with db:
        db.create_tables([Users, Items])


def convert_tables():
    pass
