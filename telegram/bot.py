import asyncio

from api import ApiClient
from models import TelegramUser, Token
from settings import config

from aiogram import Bot, Dispatcher, executor, types


tg = Bot(token=config.get("bot_token"))
client = ApiClient(config.get("host"))
dp = Dispatcher(tg)


async def auth_user(registered_user: TelegramUser):
    asyncio.create_task(client.get_token(registered_user))
    return registered_user


async def register_user(anonymous_user: TelegramUser):
    telegram_user = await client.create_user(anonymous_user)
    if isinstance(telegram_user, TelegramUser):
        return await auth_user(telegram_user)


def create_anonymous_user(msg) -> TelegramUser:
    return TelegramUser(
        telegram_id=str(msg.from_user.id),
        first_name=msg.from_user.first_name,
        last_name=msg.from_user.last_name
    )


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):

    instance: TelegramUser = create_anonymous_user(message)
    await register_user(instance)
    msg: str = "Привет 👋️ Я спорт-бот, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку\n\n" \
               "Введите /subscribe, чтобы подписаться и продолжть просмотр."

    await message.reply(msg)


@dp.message_handler(commands=["account"])
async def get_account_info(message: types.Message):

    instance: TelegramUser = create_anonymous_user(message)
    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token)
        msg: str = f"Твои данные:\n\n" \
                   f"Имя: {user.first_name}\n" \
                   f"Фамилия: {user.last_name}\n" \
                   f"Баланс: {user.balance}"
    else:
        msg = "Введите /start, чтобы начать..."

    await message.reply(msg)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_shutdown=client.clear_cache)