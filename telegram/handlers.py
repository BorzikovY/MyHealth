import asyncio
from typing import List

from aiogram import types

from api import ApiClient, create_anonymous_user, register_user, create_admin_user
from keyboards import (
    start_keyboard,
    create_filter_keyboard,
    program as program_filter,
    nutrition as nutrition_filter
)
from models import TelegramUser, Token, TrainingProgram, Nutrition, Training, Subscriber


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
    await create_subscribe(call.message)


async def create_subscribe(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.create_subscriber(instance, token)
        msg: str = f"Вы подписаны!"
    else:
        msg = "Введите /start, чтобы зарегистрироваться"
    await message.answer(msg)


async def update_subscribe(message: types.Message, data: dict):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.update_subscriber(
            instance, token,
            data=data
        )
        await get_my_health(message)
    else:
        await message.answer("Введите /start, чтобы зарегистрироваться")


async def get_my_health(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(
            instance, token, cache=True
        )
        subscriber = await client.get_subscriber(
            user, token,
            data={"telegram_id": user.subscriber},
            cache=True
        )
        if isinstance(subscriber, Subscriber):
            keyboard = types.InlineKeyboardMarkup(2).add(
                types.InlineKeyboardButton("Посмотреть программу", callback_data=program_filter.new(
                    id=subscriber.training_program if subscriber.training_program else 0
                )),
                types.InlineKeyboardButton("Обновить данные", callback_data="filter_subscribe")
            )
            await message.reply(
                subscriber.message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            await message.reply("Введите /subscribe, чтобы подписаться")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")


async def get_programs(message: types.Message, data: dict = None):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: list[TrainingProgram] = await client.get_programs(
            instance,
            token,
            data=data,
            cache=True
        )
        for program in instances:
            program_keyboard = types.InlineKeyboardMarkup(2).add(
                types.InlineKeyboardButton(
                    "Получить бесплатно ✅️",
                    callback_data="subscribe"
                ),
                types.InlineKeyboardButton(
                    text="Подробнее...",
                    callback_data=program_filter.new(
                        id=program.id
                    )
                )
            )
            await message.reply(program.message_short,
                                reply_markup=program_keyboard,
                                parse_mode="HTML")
        msg = "Список программ 🗒️" if instances else "Контента нет 😔️"
        await message.reply(msg, reply_markup=create_filter_keyboard("filter_programs", len(instances)))
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")


async def get_nutritions(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        nutritions: List[Nutrition] = await client.get_nutritions(
            instance, token,
            cache=True,
            data={}
        )
        for nutrition in nutritions:
            nutrition_keyboard = types.InlineKeyboardMarkup(2).add(
                types.InlineKeyboardButton(
                    "Получить бесплатно ✅️",
                    callback_data="subscribe"
                ),
                types.InlineKeyboardButton(
                    text="Подробнее...",
                    callback_data=nutrition_filter.new(
                        id=nutrition.id
                    )
                )
            )
            await message.reply(nutrition.message_short,
                                reply_markup=nutrition_keyboard,
                                parse_mode="HTML")
        await message.reply(
            "Список спортивных добавок" if nutritions else "Контента нет(",
            reply_markup=create_filter_keyboard("filter_nutritions", len(nutritions))
        )
    else:
        await message.reply("Введите /start, чтобы начать...")


async def get_trainings(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        trainings: List[Training] = await client.get_trainings(
            instance, token,
            cache=True, data={}
        )
        msg = "Список тренировок"
        for training in trainings:
            msg += f"\n\n{training.name}:\n" \
                   f"Описание: {training.description}"
        await message.reply(msg if msg else "Контента нет(")
    else:
        await message.reply("Введите /start, чтобы начать...")


async def get_program(call: types.CallbackQuery, callback_data: dict):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(data=call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        id = int(callback_data.get("id", 0))
        program: TrainingProgram = await client.get_program(
            instance, token,
            cache=True,
            data={"id": id}
        )
        if isinstance(program, TrainingProgram):
            await call.message.answer(program.message, parse_mode="HTML")
        else:
            await call.message.answer("Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


async def get_nutrition(call: types.CallbackQuery, callback_data: dict):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        id = int(callback_data.get("id", 0))
        nutrition: Nutrition = await client.get_nutrition(
            instance, token,
            cache=True,
            data={"id": id}
        )
        if isinstance(nutrition, Nutrition):
            await call.message.answer(nutrition.message, parse_mode="HTML")
        else:
            await call.message.answer("Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")
