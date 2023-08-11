from datetime import timedelta, datetime
from typing import List

import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from api import (
    Telegram,
    get_programs,
    get_nutritions,
    update_subscribe,
    get_trainings,
    get_portions, get_approaches
)
from keyboards import (
    schedule_keyboard,
    gender_keyboard,
    create_op_keyboard,
    create_content_keyboard,
    create_move_keyboard,
    create_training_keyboard, location_keyboard
)
from notifications import scheduler


class ProgramState(StatesGroup):
    program_filter: State = State()
    difficulty_value: State = State()
    difficulty_op: State = State()
    weeks_value: State = State()
    weeks_op: State = State()
    next_program: State = State()
    next_training: State = State()


class NutritionState(StatesGroup):
    nutrition_filter: State = State()
    next_nutrition: State = State()
    next_portion: State = State()


class ApproachState(StatesGroup):
    next_approach: State = State()


class SubscribeState(StatesGroup):
    age: State = State()
    height: State = State()
    weight: State = State()
    gender: State = State()


class CaloriesState(StatesGroup):
    activity: State = State()


class ScheduleState(StatesGroup):
    weekdays: State = State()
    location: State = State()
    time: State = State()


class Iterable:

    def __init__(self, iterable: List):
        self.loop = iterable

    def __iter__(self):
        self._count = -1
        return self

    def __next__(self, *args, **kwargs):
        try:
            self._count += 1
            return self.loop[self._count]
        except IndexError:
            raise StopIteration("No content")


class Cycle(Iterable):

    def __next__(self, direction: int = 1):
        try:
            self._count = (self._count + direction) % len(self.loop)
            return self.loop[self._count]
        except ZeroDivisionError:
            raise ValueError("No content")


async def send_approach(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    approaches = (await state.get_data()).get("approaches", [])
    approach = approaches.__next__(direction)
    await call.message.edit_text(approach.message, parse_mode="HTML")
    await call.message.edit_reply_markup(
        create_training_keyboard()
    )
    await state.update_data({"approaches": approaches})
    await ApproachState.next_approach.set()


async def get_next_approach(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    if direction == 0:
        trainings = (await state.get_data()).get("trainings")
        try:
            instances = iter(
                Cycle(await get_approaches(
                    call.from_user, {"training_id": next(trainings)}
                ))
            )
            await state.update_data({"trainings": trainings, "approaches": instances})
        except StopIteration as error:
            await call.message.edit_text("Программа закончилась. Введите /approaches, чтобы еще раз все посмотреть.")
            return
    await send_approach(call, state, direction)


async def send_notification(chat_id):
    await Telegram.send_message(
        chat_id,
        "Пора тренироваться! Введите /approaches, чтобы просмотреть список упражнений."
    )


async def set_notification(message: types.Message, state: FSMContext):
    data = await state.get_data()
    offset = datetime.now(
        tz=pytz.timezone(data["timezone"])
    ).utcoffset().total_seconds() // 3600

    scheduler.add_job(
        send_notification,
        trigger="cron",
        kwargs={"chat_id": message.from_user.id},
        day_of_week=",".join(data["weekdays"]),
        hour=data["hour"] - int(offset),
        minute=data["minute"],
        id=str(message.from_user.id),
        replace_existing=True
    )


async def get_weekdays(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    if callback_data.get("filter", "0") == "1":
        await call.message.edit_text("Выберите день недели")
        await call.message.edit_reply_markup(
            reply_markup=schedule_keyboard
        )
        weekdays = data.get("weekdays", set())
        if callback_data.get("weekday").isdigit():
            weekdays.update({callback_data.get("weekday")})
        await state.update_data({"weekdays": weekdays})
        await ScheduleState.weekdays.set()
    else:
        if not data.get("weekdays"):
            await state.update_data({"weekdays": {"0", "1", "2", "3", "4"}})
        await call.message.delete()
        await Telegram.send_message(
            call.from_user.id,
            "Введите город, в котором живете (необходимо для настройки времени)"
        )
        await ScheduleState.location.set()


async def get_location(message: types.Message, state: FSMContext):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(message.text)

    timezone = TimezoneFinder().timezone_at(
        lng=location.longitude, lat=location.latitude
    )

    await state.update_data({"timezone": timezone})
    await Telegram.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()
    await Telegram.send_message(message.from_user.id, "Введите время в формате HH:MM")
    await ScheduleState.next()


async def get_time(message: types.Message, state: FSMContext):
    try:
        hours, minutes = (int(value) for value in message.text.split(":"))
        time = timedelta(hours=hours, minutes=minutes)
        assert timedelta(hours=0, minutes=0) <= time <= timedelta(hours=23, minutes=59)
        await state.update_data(
            {
                "hour": hours,
                "minute": minutes
             }
        )
        await set_notification(message, state)
        await message.answer("Уведомление установлено!")
        await state.finish()
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите время от 00:00 до 23:59")
        await ScheduleState.time.set()
    await Telegram.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_age(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert 0 <= value <= 100
        await state.update_data(age=value)
        await Telegram.send_message(message.from_user.id, "Введите рост 📏️ (в метрах)")
        await SubscribeState.next()
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите целое число от 0 до 100")
        await SubscribeState.height.set()
    await Telegram.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_height(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1. <= value <= 3.
        await state.update_data(height=value)
        await Telegram.send_message(message.from_user.id, "Введите вес ⚖️ (в кг)")
        await SubscribeState.next()
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите десятичное число от 1 до 3")
        await SubscribeState.height.set()
    await Telegram.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_weight(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 20. <= value <= 220.
        await state.update_data(weight=value)
        await Telegram.send_message(message.from_user.id, "Выберите гендер 👨️/👩️/🚁️", reply_markup=gender_keyboard)
        await SubscribeState.next()
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите десятичное число от 20 до 220")
        await SubscribeState.weight.set()
    await Telegram.delete_message(
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

async def get_activity(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    activity = float(callback_data.get('activity'))
    data = await state.get_data()
    match data['gender']:
        case 'male':
            calories = ((10 * data['weight']) + (625 * data['height']) - (5 * data['age'] + 5)) * activity
        case 'female':
            calories = ((10 * data['weight']) + (625 * data['height']) - (5 * data['age'] - 161)) * activity
    await call.message.edit_text(f'Дневная норма калорий: {calories}')
    await state.finish()


async def send_nutritions(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    nutritions = (await state.get_data()).get("nutritions", [])
    try:
        nutrition = nutritions.__next__(direction)
        await call.message.edit_text(nutrition.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            create_content_keyboard(nutrition)
        )
        await state.update_data({"nutritions": nutritions, "id": nutrition.id})
        await NutritionState.next_nutrition.set()
    except ValueError:
        await call.message.edit_text("Контента нет")
        await state.finish()


async def send_portions(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    portions = (await state.get_data()).get("portions", [])
    try:
        portion = portions.__next__(direction)
        await call.message.edit_text(portion.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            create_move_keyboard()
        )
        await state.update_data({"portions": portions})
        await NutritionState.next_portion.set()
    except ValueError:
        await call.answer("Контента нет", show_alert=True)
        await NutritionState.next_nutrition.set()


async def get_nutrition_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.update_data({"nutritions": iter(Cycle(
        await get_nutritions()
    ))})
    await send_nutritions(call, state)


async def get_next_nutrition(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    if direction != 0:
        await send_nutritions(call, state, direction)
    else:
        data = await state.get_data()
        await state.update_data({"portions": iter(Cycle(
            await get_portions({"nutrition_id": data.get("id", 0)})
        ))})
        await send_portions(call, state, direction)


async def get_next_portion(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    if direction != 0:
        await send_portions(call, state, direction)
    else:
        await state.set_state({"portions": None})
        await send_nutritions(call, state, direction)


async def send_programs(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    programs = (await state.get_data()).get("programs", [])
    try:
        program = programs.__next__(direction)
        await call.message.edit_text(program.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            create_content_keyboard(program, training_program=program.id)
        )
        await state.update_data({"programs": programs, "id": program.id})
        await ProgramState.next_program.set()
    except ValueError:
        await call.message.edit_text("Контента нет")
        await state.finish()


async def send_trainings(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    trainings = (await state.get_data()).get("trainings", [])
    try:
        training = trainings.__next__(direction)
        await call.message.edit_text(training.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            create_move_keyboard()
        )
        await state.update_data({"trainings": trainings})
        await ProgramState.next_training.set()
    except ValueError:
        await call.answer("Контента нет", show_alert=True)
        await ProgramState.next_program.set()


async def get_program_filter(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if callback_data.get("filter", "0") == "1":
        await call.message.edit_text("Введите уровень сложности (от 1.00 до 5.00)")
        await ProgramState.next()
    else:
        await state.update_data({"programs": iter(Cycle(await get_programs()))})
        await send_programs(call, state)


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
    await Telegram.delete_message(
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
    await Telegram.delete_message(
        message.from_user.id, message.message_id - 1
    )
    await message.delete()


async def get_weeks_op(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    data = await state.get_data()
    data["weeks"] = callback_data.get("weeks") + data.get("weeks")
    await state.update_data({"programs": iter(Cycle(await get_programs(data)))})
    await send_programs(call, state)


async def get_next_program(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    if direction != 0:
        await send_programs(call, state, direction)
    else:
        data = await state.get_data()
        await state.update_data({"trainings": iter(Cycle(
            await get_trainings({"program_id": data.get("id", 0)})
        ))})
        await send_trainings(call, state, direction)


async def get_next_training(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    direction = int(callback_data.get("direction"))
    if direction != 0:
        await send_trainings(call, state, direction)
    else:
        await state.set_state({"trainings": None})
        await send_programs(call, state, direction)
