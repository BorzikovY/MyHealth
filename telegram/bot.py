from api import ApiClient
from models import TelegramUser, Token, TrainingProgram, Nutrition, Training
from handlers import send_welcome, get_account_info, subscribe, get_programs, get_programs
from states import (
    program_filter_start,
    get_difficulty_value,
    get_difficulty_op,
    get_weeks_value,
    get_weeks_op,
    finish_program_filter,
    ProgramFilter,
)
from keyboards import create_filter_keyboard, del_filter, program_filter, week_filter, difficulty_filter
from settings import config

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from typing import List

tg = Bot(token=config.get("bot_token"))
storage = MemoryStorage()
dp = Dispatcher(tg, storage=storage)


@dp.callback_query_handler(del_filter.filter())
async def delete_messages(call: types.CallbackQuery, callback_data: dict):
    current_id, messages = int(call.message.message_id) - 1, int(callback_data.get("messages"))
    for _id in range(current_id, current_id-messages, -1):
        await tg.delete_message(call.message.chat.id, _id)
    await tg.delete_message(call.message.chat.id, current_id + 1)
    await tg.send_message(
        call.message.chat.id, "Список программ 🗒️",
        reply_markup=create_filter_keyboard()
    )


dp.register_message_handler(send_welcome, commands=["start"])
dp.register_message_handler(get_account_info, commands=["account"])
dp.register_callback_query_handler(subscribe, text="subscribe")
dp.register_message_handler(get_programs, commands=["programs"])
dp.register_callback_query_handler(program_filter_start, text="filter_programs"),
dp.register_callback_query_handler(
    get_difficulty_value,
    program_filter.filter(),
    state=ProgramFilter.difficulty_value
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
        programs: List[TrainingProgram] = await client.get_programs(instance, token)
        msg = "Список програм"
        for program in programs:
            msg += f"\n\n{program.name}:\n" \
                   f"Описание: {program.description}"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


@dp.callback_query_handler(text="nutritions")
async def nutritions(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        nutritions: List[Nutrition] = await client.get_nutritions(instance, token)
        msg = "Список спортивных добавок"
        for nutrition in nutritions:
            msg += f"\n\n{nutrition.name}:\n" \
                   f"Описание: {nutrition.description}"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


@dp.callback_query_handler(text="trainings")
async def trainings(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        trainings: List[Training] = await client.get_trainings(instance, token)
        print(trainings)
        msg = "Список тренировок"
        for training in trainings:
            msg += f"\n\n{training.name}:\n" \
                   f"Описание: {training.description}"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


@dp.callback_query_handler(text="program")
async def program(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(data=call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        program: TrainingProgram = await client.get_program(instance, token)
        msg: str = f"{program.name}\n" \
                   f"{program.description}\n" \
                   f"{program.image}\n"\
                   f"Кол-во недель: {program.weeks}\n"\
                   f"Кол-во тренировок: {program.training_count}\n"\
                   f"Среднее время тренировки: {program.avg_training_time}\n"\
                   f"Сложность: {program.difficulty}n"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


@dp.callback_query_handler(text="nutrition")
async def program(call: types.CallbackQuery):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        nutrition: Nutrition = await client.get_nutrition(instance, token)
        msg: str = f"{nutrition.name}\n" \
                   f"{nutrition.description}\n" \
                   f"{nutrition.dosages}\n"\
                   f"Кол-во недель: {nutrition.use}\n"\
                   f"Кол-во тренировок: {nutrition.contraindications}\n"
        await call.message.answer(msg if msg else "Контента нет(")
    else:
        await call.message.answer("Введите /start, чтобы начать...")


start_keyboard = types.InlineKeyboardMarkup(4).add(
    types.InlineKeyboardButton(text="Подписаться 🎁", callback_data="subscribe"),
    types.InlineKeyboardButton(text="Я только посмотреть 😏️", callback_data="programs"),
    types.InlineKeyboardButton(text="Список спортивных добавок", callback_data="nutritions"),
    types.InlineKeyboardButton(text="Список тренировок", callback_data="trainings"),
    types.InlineKeyboardButton(text="Первая тренировочная программа", callback_data="program"),
    types.InlineKeyboardButton(text="Первая спортивная добавка", callback_data="nutrition")
)
dp.register_message_handler(get_difficulty_op, state=ProgramFilter.difficulty_op)
dp.register_callback_query_handler(
    get_weeks_value,
    difficulty_filter.filter(),
    state=ProgramFilter.weeks_value)
dp.register_message_handler(get_weeks_op, state=ProgramFilter.weeks_op)
dp.register_callback_query_handler(
    finish_program_filter,
    week_filter.filter(),
    state=ProgramFilter.finish_filter)


if __name__ == '__main__':
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=ApiClient().update_cache,
        on_shutdown=ApiClient().clear_cache
    )
