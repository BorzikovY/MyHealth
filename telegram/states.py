from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from handlers import get_programs, get_nutritions, update_subscribe
from keyboards import program_filter, difficulty_filter, week_filter, gender_filter


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


async def start_subscribe_filter(call: types.CallbackQuery):
    await call.bot.send_message(
        call.message.chat.id,
        "Введите возраст",
    )
    await SubscribeState.age.set()


async def get_age(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert 0 <= value <= 100
        await state.update_data(age=value)
        await message.answer("Введите рост")
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите целое число от 0 до 100")
        await SubscribeState.height.set()


async def get_height(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1. <= value <= 3.
        await state.update_data(height=value)
        await message.answer("Введите вес")
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите десятичное число от 1 до 3")
        await SubscribeState.height.set()


async def get_weight(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 20. <= value <= 220.
        await state.update_data(weight=value)
        keyboard = types.InlineKeyboardMarkup(3).add(
            types.InlineKeyboardButton("мужской", callback_data=gender_filter.new(
                gender="male"
            )),
            types.InlineKeyboardButton("женский", callback_data=gender_filter.new(
                gender="female"
            )),
            types.InlineKeyboardButton("другой", callback_data=gender_filter.new(
                gender="helicopter"
            )),
        )
        await message.answer("Выберите гендер", reply_markup=keyboard)
        await SubscribeState.next()
    except Exception:
        await message.answer("Введите десятичное число от 20 до 220")
        await SubscribeState.weight.set()


async def get_gender(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["gender"] = callback_data.get("gender")
    await update_subscribe(call.message, data)
    await state.finish()


async def nutrition_filter_start(call: types.CallbackQuery):
    await get_nutritions(call.message)


async def program_filter_start(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup(2).add(
        types.InlineKeyboardButton("Да", callback_data=program_filter.new(
            filter=1
        )),
        types.InlineKeyboardButton("Нет", callback_data=program_filter.new(
            filter=0
        )),
    )
    await call.bot.send_message(
        call.message.chat.id,
        "Включить в подборку фильтрацию?",
        reply_markup=keyboard
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
        keyboard = types.InlineKeyboardMarkup(3).add(
            types.InlineKeyboardButton("🔼️", callback_data=difficulty_filter.new(
                difficulty=">"
            )),
            types.InlineKeyboardButton(f"{value}", callback_data=difficulty_filter.new(
                difficulty="="
            )),
            types.InlineKeyboardButton("🔽️", callback_data=difficulty_filter.new(
                difficulty="<"
            ))
        )
        await message.answer("Введите операцию с числом", reply_markup=keyboard)
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
        keyboard = types.InlineKeyboardMarkup(3).add(
            types.InlineKeyboardButton(f"🔼️", callback_data=week_filter.new(
                weeks=">"
            )),
            types.InlineKeyboardButton(f"{value}", callback_data=week_filter.new(
                weeks="="
            )),
            types.InlineKeyboardButton("🔽️", callback_data=week_filter.new(
                weeks="<"
            ))
        )
        await message.answer("Введите операцию с числом", reply_markup=keyboard)
        await ProgramFilter.next()
    except Exception:
        await message.answer("Введите число больше 0")
        await ProgramFilter.weeks_value.set()


async def finish_program_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["weeks"] = callback_data.get("weeks") + data.get("weeks")
    await get_programs(call.message, data)
    await state.finish()
