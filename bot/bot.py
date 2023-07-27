from api import ApiClient
from settings import config

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(token=config.get("bot_token"))
client = ApiClient(config.get("host"))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):

    msg: str = "Привет 👋️ Я спорт-бот, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку\n\n" \
               "Введите /subscribe, чтобы подписаться и продолжть просмотр."

    await message.reply(msg)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)