import os
from dotenv import dotenv_values


config = dotenv_values(os.environ.get("env_file"))
SECRET_KEY = config.get("secret_key")
HOST = config.get("host")