import os
import logging


TOKEN_ID = os.environ['TOKEN_SHOPPING_LIST']


class Config:
    PORT = int(os.environ.get("PORT", 5000))
    TELEGRAM_TOKEN = os.environ.get("TOKEN_SHOPPING_LIST", "")
    MODE = os.environ.get("MODE", "polling")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    HEROKU_APP_NAME = os.environ.get("APP_NAME", "")

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    @staticmethod
    def init_logging():
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            level=Config.LOG_LEVEL)