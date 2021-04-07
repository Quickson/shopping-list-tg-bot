
from models.create_tables import create_tables
from bot import BotBL


if __name__ == '__main__':
    create_tables()
    bot = BotBL()
    bot.start()
