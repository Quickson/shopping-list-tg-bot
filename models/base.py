from peewee import *
from const import Config

db = PostgresqlDatabase(Config.DB_NAME, user=Config.DB_USER, host=Config.DB_HOST,
                        password=Config.DB_PASSWORD)


class BaseModel(Model):
    class Meta:
        database = db
