import os
from dotenv import dotenv_values


config = dotenv_values(os.environ.get("env_file"))
SECRET_KEY = config.get("secret_key")
HOST = config.get("host")
BOT_TOKEN = config.get("bot_token")
ADMIN_TELEGRAM_ID = config.get("admin_telegram_id")
ADMIN_CHAT_ID = config.get("admin_chat_id")
CACHE_UPDATE_TIME = int(config.get("cache_update_time"))

DB_URL = config.get("db_url")
