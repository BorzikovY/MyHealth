import asyncio

from api import ApiClient
from models import TelegramUser, Token, TrainingProgram, Subscriber
from settings import config

from aiogram import Bot, Dispatcher, executor, types


tg = Bot(token=config.get("bot_token"))
dp = Dispatcher(tg)


async def auth_user(client, registered_user: TelegramUser):
    asyncio.create_task(client.get_token(registered_user))
    return registered_user


async def register_user(client, anonymous_user: TelegramUser):
    telegram_user = await client.create_user(anonymous_user)
    if isinstance(telegram_user, TelegramUser):
        return await auth_user(client, telegram_user)


def create_anonymous_user(data) -> TelegramUser:
    return TelegramUser(
        telegram_id=str(data.id),
        first_name=data.first_name,
        last_name=data.last_name
    )


def create_admin_user() -> TelegramUser:
    return TelegramUser(
        telegram_id=config.get("admin_telegram_id"),
        chat_id=config.get("admin_chat_id")
    )


@dp.callback_query_handler(text="subscribe")
async def subscribe(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.create_subscriber(instance, token)
        msg: str = f"Вы подписаны!"
    else:
        msg = "Введите /start, чтобы начать..."

    await call.message.answer(msg)


@dp.callback_query_handler(text="programs")
async def programs(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        programs: list[TrainingProgram] = await client.get_programs(instance, token)
        msg = "Список програм"
        for program in programs:
            msg += f"\n\n{program.name}:\n" \
                   f"Описание: {program.description}"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


start_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton(text="Подписаться 🎁", callback_data="subscribe"),
    types.InlineKeyboardButton(text="Я только посмотреть 😏️", callback_data="programs")
)


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    await register_user(client, instance)
    msg: str = "Привет 👋️ Я спорт-бот, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку\n\n" \
               "Введите /subscribe, чтобы подписаться и продолжть просмотр."

    await message.reply(msg, reply_markup=start_keyboard)


@dp.message_handler(commands=["account"])
async def get_account_info(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

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
    executor.start_polling(dp, skip_updates=True, on_shutdown=ApiClient().clear_cache)