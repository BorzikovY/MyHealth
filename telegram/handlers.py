import asyncio
from aiogram import types

from api import ApiClient, create_anonymous_user, register_user, create_admin_user
from keyboards import start_keyboard, create_filter_keyboard
from models import (
    TelegramUser,
    Token,
    TrainingProgram,
    Subscriber
)


async def send_welcome(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    await register_user(client, instance)
    msg: str = "Привет 👋️ Я *спорт\-бот*, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку"

    await message.reply(msg, reply_markup=start_keyboard, parse_mode="MarkdownV2")


async def get_account_info(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        msg = user.message
    else:
        msg = "Введите /start, чтобы зарегистрироваться"

    await message.reply(msg, parse_mode="HTML")


async def subscribe(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.create_subscriber(instance, token)
        msg: str = f"Вы подписаны!"
    else:
        msg = "Введите /start, чтобы зарегистрироваться"

    await call.message.answer(msg)


async def get_programs(message: types.Message, data: dict = None):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: list[TrainingProgram] = await client.get_programs(instance, token, data=data, cache=True)
        for program in instances:
            program_keyboard = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Бесплатно ✅️", callback_data="subscribe"),
            )
            await message.reply(program.message,
                                reply_markup=program_keyboard,
                                parse_mode="HTML")
        msg = "Список программ 🗒️" if instances else "Контента нет 😔️"
        await message.reply(msg,
                            reply_markup=create_filter_keyboard(len(instances)))
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")
