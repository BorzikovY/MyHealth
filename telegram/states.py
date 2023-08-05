from datetime import timedelta
from typing import List

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from api import get_programs, get_nutritions, update_subscribe
from keyboards import (
    schedule_keyboard,
    start_schedule_keyboard,
    gender_keyboard,
    create_op_keyboard,
    create_content_keyboard
)


class ProgramState(StatesGroup):
    program_filter: State = State()
    difficulty_value: State = State()
    difficulty_op: State = State()
    weeks_value: State = State()
    weeks_op: State = State()
    next_program: State = State()


class NutritionState(StatesGroup):
    nutrition_filter: State = State()
    next_nutrition: State = State()


class SubscribeState(StatesGroup):
    age: State = State()
    height: State = State()
    weight: State = State()
    gender: State = State()


class ScheduleState(StatesGroup):
    weekdays: State = State()
    time: State = State()


class Cycle:

    def __init__(self, iterable: List):
        self.loop = iterable

    def __iter__(self):
        self._count = 0
        return self

    def __next__(self, direction: int):
        self._count = (self._count + direction) % len(self.loop)
        return self.loop[self._count]


async def start_schedule_filter(call: types.CallbackQuery):
    msg = "Сконфигурируйте расписание самостоятельно или\n " \
          "используйте параметры по умолчанию\n\n" \
          "(уведомления будут приходить с понедельника по пятницу)"
    await call.bot.send_message(
        call.message.chat.id,
        msg,
        reply_markup=start_schedule_keyboard
    )
    await ScheduleState.weekdays.set()


async def get_weekdays(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data.get("filter", "0") == "1":
        await call.bot.send_message(
            call.message.chat.id,
            text="Выберите день недели",
            reply_markup=schedule_keyboard
        )
        await ScheduleState.weekdays.set()
    else:
        data = await state.get_data()
        if not data.get("weekdays"):
            await state.update_data({"weekdays": [0, 1, 2, 3, 4]})
        await call.answer("Введите время в формате HH:MM")
        await ScheduleState.next()


async def get_time(message: types.Message, state: FSMContext):
    try:
        hours, minutes = (int(value) for value in message.text.split(":"))
        time = timedelta(hours=hours, minutes=minutes)
        assert timedelta(hours=0, minutes=0) <= time <= timedelta(hours=23, minutes=59)
        await message.answer("Уведомление установлено!")
        await state.finish()
    except Exception as error:
        print(error)
        await message.answer("Введите время от 00:00 до 23:59")
        await ScheduleState.time.set()


async def get_age(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert 0 <= value <= 100
        await state.update_data(age=value)
        await message.answer("Введите рост 📏️ (в метрах)")
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите целое число от 0 до 100")
        await SubscribeState.height.set()
    await message.bot.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_height(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1. <= value <= 3.
        await state.update_data(height=value)
        await message.answer("Введите вес ⚖️ (в кг)")
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите десятичное число от 1 до 3")
        await SubscribeState.height.set()
    await message.bot.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_weight(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 20. <= value <= 220.
        await state.update_data(weight=value)
        await message.answer("Выберите гендер 👨️/👩️/🚁️", reply_markup=gender_keyboard)
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите десятичное число от 20 до 220")
        await SubscribeState.weight.set()
    await message.bot.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_gender(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["gender"] = callback_data.get("gender")
    if await update_subscribe(call.from_user, data):
        await call.message.edit_text("Данные были успешно обновлены!")
    else:
        await call.message.edit_text("Что-то пошло не так")
    await state.finish()


async def send_nutritions(message: types.Message, state: FSMContext, direction: int = 1):
    nutritions = (await state.get_data()).get("nutritions", [])
    nutrition = nutritions.__next__(direction)
    await message.edit_text(nutrition.message_short, parse_mode="HTML")
    await message.edit_reply_markup(
        create_content_keyboard(nutrition, sport_nutrition=nutrition.id)
    )
    await state.update_data({"nutritions": nutritions})
    await NutritionState.next_nutrition.set()


async def get_nutrition_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.update_data({"nutritions": iter(Cycle(
        await get_nutritions()
    ))})
    await send_nutritions(call.message, state)


async def get_next_nutrition(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    await send_nutritions(call.message, state, direction)


async def send_programs(message: types.Message, state: FSMContext, direction: int = 1):
    programs = (await state.get_data()).get("programs", [])
    program = programs.__next__(direction)
    await message.edit_text(program.message_short, parse_mode="HTML")
    await message.edit_reply_markup(
        create_content_keyboard(program, training_program=program.id)
    )
    await state.update_data({"programs": programs})
    await ProgramState.next_program.set()


async def get_program_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data.get("filter", "0") == "1":
        await call.message.edit_text("Введите уровень сложности (от 1.00 до 5.00)")
        await ProgramState.next()
    else:
        await state.update_data({"programs": iter(Cycle(await get_programs()))})
        await send_programs(call.message, state)


async def get_difficulty_value(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1 <= value <= 5
        await state.update_data(difficulty=message.text)
        await message.bot.send_message(
            message.from_user.id,
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("difficulty", value)
        )
        await ProgramState.next()
    except (AssertionError, ValueError) as valid_error:
        await message.answer("Введите десятичное число от 1 до 5")
        await ProgramState.difficulty_op.set()
    await message.bot.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_difficulty_op(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    await state.update_data(difficulty=callback_data.get("difficulty") + data.get("difficulty"))
    await call.message.edit_text("Введите количество недель")
    await ProgramState.next()


async def get_weeks_value(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert value > 0
        await state.update_data(weeks=message.text)
        await message.bot.send_message(
            message.from_user.id,
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("weeks", value)
        )
        await ProgramState.next()
    except (AssertionError, ValueError) as valid_error:
        await message.answer("Введите число больше 0")
        await ProgramState.weeks_op.set()
    await message.bot.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_weeks_op(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["weeks"] = callback_data.get("weeks") + data.get("weeks")
    await state.update_data({"programs": iter(Cycle(await get_programs(data)))})
    await send_programs(call.message, state)


async def get_next_program(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    await send_programs(call.message, state, direction)
