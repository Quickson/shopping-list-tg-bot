from peewee import *
import os

# db = PostgresqlDatabase(os.environ['DB_NAME'], user=os.environ['DB_USER'], host=os.environ['DB_HOST'],
#                         password=os.environ['DB_PASSWORD'])

db = PostgresqlDatabase('test', user='postgres', host='localhost',
                        password='postgres')


class BaseModel(Model):
    class Meta:
        database = db
