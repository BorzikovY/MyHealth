from typing import List

from aiogram import types
from aiogram.dispatcher import FSMContext

from api import ApiClient, create_anonymous_user, register_user, create_admin_user
from keyboards import (
    start_keyboard,
    create_my_health_keyboard,
    filter_keyboard
)
from states import (
    ProgramState,
    NutritionState,
    SubscribeState
)
from models import (
    TelegramUser,
    Token,
    TrainingProgram,
    Nutrition,
    Training
)
from notifications import scheduler


async def start(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    await register_user(client, instance)
    msg: str = "Привет 👋️ Я *спорт\-бот*, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку"

    await message.reply(msg, reply_markup=start_keyboard, parse_mode="MarkdownV2")


async def account(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        msg = user.message
    else:
        msg = "Введите /start, чтобы зарегистрироваться"

    await message.reply(msg, parse_mode="HTML")


async def subscribe(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.create_subscriber(instance, token)
        msg: str = f"Вы подписаны!"
    else:
        msg = "Введите /start, чтобы зарегистрироваться"
    await message.answer(msg)


async def programs(message: types.Message, state: FSMContext):
    await state.finish()
    await message.bot.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=filter_keyboard
    )
    await ProgramState.program_filter.set()


async def nutritions(message: types.Message, state: FSMContext):
    await state.finish()
    await message.bot.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=filter_keyboard
    )
    await NutritionState.nutrition_filter.set()


async def my_health(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        if subscriber := user.subscriber:
            await message.reply(
                subscriber.message,
                parse_mode="HTML",
                reply_markup=create_my_health_keyboard(
                    sport_nutrition=subscriber.sport_nutrition,
                    training_program=subscriber.training_program
                )
            )
        else:
            await message.reply("Введите /subscribe, чтобы подписаться")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")


async def update_subscribe(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(
        "Введите возраст 👶️-🧓️",
    )
    await SubscribeState.age.set()


async def get_trainings(message: types.Message, data: dict = None):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        trainings: List[Training] = await client.get_trainings(
            instance, token,
            cache=True, data=data
        )
        for training in trainings:
            await message.reply(training.message_short, parse_mode="HTML")
        await message.reply(
            "Список тренировок" if trainings else "Контента нет("
        )
    else:
        await message.reply("Введите /start, чтобы начать...")


async def get_approaches(message: types.Message):
    pass


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
            msg = "Вы еще не преобрели тренировочную программу\n\n" \
                  "Введите /programs, чтобы просмотреть список доступных программ"
            await call.message.answer(msg)
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
            msg = "Вы еще не преобрели подписку на спортивное питание\n\n" \
                  "Введите /nutritions, чтобы просмотреть список спортивного питания"
            await call.message.answer(msg)
    else:
        await call.message.answer("Введите /start, чтобы начать...")


async def get_training(call: types.CallbackQuery, callback_data: dict):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        id = int(callback_data.get("id", 0))
        training: Training = await client.get_training(
            instance, token,
            data={"id": id}
        )
        if isinstance(training, Training):
            keyboard = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("Список упражнений", callback_data="approaches")
            )
            await call.message.answer(
                training.message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            msg = "Вы еще не преобрели тренировочную программу\n\n" \
                  "Введите /programs, чтобы просмотреть список доступных программ"
            await call.message.answer(msg)
    else:
        await call.message.answer("Введите /start, чтобы начать...")


async def send_notification(message: types.Message):
    await message.bot.send_message(
        message.from_user.id,
        "Пора тренироваться!"
    )
