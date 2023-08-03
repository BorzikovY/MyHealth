from datetime import timedelta

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from handlers import get_programs, get_nutritions, update_subscribe
from keyboards import (
    schedule_keyboard,
    start_schedule_keyboard,
    gender_keyboard,
    start_program_keyboard,
    create_op_keyboard
)


class ProgramFilter(StatesGroup):
    difficulty_value: State = State()
    difficulty_op: State = State()
    weeks_value: State = State()
    weeks_op: State = State()
    finish_filter: State = State()


class SubscribeState(StatesGroup):
    age: State = State()
    height: State = State()
    weight: State = State()
    gender: State = State()


class ScheduleState(StatesGroup):
    weekdays: State = State()
    time: State = State()


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


async def start_subscribe_filter(call: types.CallbackQuery):
    await call.bot.send_message(
        call.message.chat.id,
        "Введите возраст 👶️-🧓️",
    )
    await SubscribeState.age.set()


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


async def get_gender(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["gender"] = callback_data.get("gender")
    data["message"] = "Данные успешно обновлены! 😉️"
    await update_subscribe(call.message, data)
    await state.finish()


async def nutrition_filter_start(call: types.CallbackQuery):
    await get_nutritions(call.message)


async def start_program_filter(call: types.CallbackQuery):
    await call.bot.send_message(
        call.message.chat.id,
        "Включить в подборку фильтрацию?",
        reply_markup=start_program_keyboard
    )
    await ProgramFilter.difficulty_value.set()


async def get_difficulty_value(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data.get("filter", "0") == "1":
        await call.answer("Введите уровень сложности (от 1.00 до 5.00)")
        await ProgramFilter.next()
    else:
        await get_programs(call.message)
        await state.finish()


async def get_difficulty_op(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1 <= value <= 5
        await state.update_data(difficulty=message.text)
        await message.answer(
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("difficulty", value)
        )
        await ProgramFilter.next()
    except Exception:
        await message.answer("Введите десятичное число от 1 до 5")
        await ProgramFilter.difficulty_op.set()


async def get_weeks_value(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    await state.update_data(difficulty=callback_data.get("difficulty") + data.get("difficulty"))
    await call.answer("Введите количество недель")
    await ProgramFilter.next()


async def get_weeks_op(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert value > 0
        await state.update_data(weeks=message.text)
        await message.answer(
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("weeks", value)
        )
        await ProgramFilter.next()
    except Exception:
        await message.answer("Введите число больше 0")
        await ProgramFilter.weeks_op.set()


async def finish_program_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["weeks"] = callback_data.get("weeks") + data.get("weeks")
    await get_programs(call.message, data)
    await state.finish()
