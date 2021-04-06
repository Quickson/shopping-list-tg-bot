import os
import logging


class Config:
    PORT = int(os.environ.get("PORT", 5000))
    TELEGRAM_TOKEN = os.environ.get("TOKEN_SHOPPING_LIST", "")
    MODE = os.environ.get("MODE", "polling")
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    HEROKU_APP_NAME = os.environ.get("APP_NAME", "")

    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

    DB_NAME = os.environ.get("DB_NAME", "test")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

    @staticmethod
    def init_logging():
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            level=Config.LOG_LEVEL)