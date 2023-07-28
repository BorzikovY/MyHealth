import os
from dotenv import dotenv_values


config = dotenv_values('.env.dev')
SECRET_KEY = config.get('secret_key')