from datetime import timedelta, datetime
from typing import List

import pytz
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from aiogram import types


from api import (
    Telegram,
    get_programs,
    update_subscribe,
    get_trainings,
    get_portions, get_approaches
)
from keyboards import (
    create_schedule_keyboard,
    create_gender_keyboard,
    create_op_keyboard,
    create_content_keyboard,
    create_move_keyboard,
    create_training_keyboard,
    Move,
    Schedule,
    Subscriber,
    Program,
    Info,
    Activity
)
from messages import (
    info_my_health_message,
    info_approaches_message
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


class InfoState(StatesGroup):
    info: State = State()


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
    await call.message.edit_text(text=approach.message, parse_mode="HTML")
    await call.message.edit_reply_markup(reply_markup=create_training_keyboard())
    await state.update_data({"approaches": approaches})
    await state.set_state(ApproachState.next_approach)


async def get_next_approach(call: types.CallbackQuery, callback_data: Move, state: FSMContext):
    if callback_data.direction == 0:
        trainings = (await state.get_data()).get("trainings")
        try:
            instances = iter(
                Cycle(await get_approaches(
                    call.from_user, {"training_id": next(trainings)}
                ))
            )
            await state.update_data({"trainings": trainings, "approaches": instances})
        except StopIteration as error:
            await call.message.edit_text(
                "Программа закончилась. Нажмите на кнопку <b>Текущая тренировка ⏳</b>, "
                "чтобы еще раз все просмотреть.",
                parse_mode="HTML"
            )
            return
    await send_approach(call, state, callback_data.direction)


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
        day_of_week=",".join(map(str, data["weekdays"])),
        hour=(data["hour"] - int(offset)) % 24,
        minute=data["minute"],
        id=str(message.from_user.id),
        replace_existing=True
    )


async def get_weekdays(call: types.CallbackQuery, callback_data: Schedule, state: FSMContext):
    data = await state.get_data()
    weekdays, texts = data.get("weekdays", set()), data.get("texts", set())

    if callback_data.filtered:
        if callback_data.weekday is not None:
            weekdays.update({callback_data.weekday})
            texts.update({callback_data.text})
        message = "Выберите день недели.\n"
        if texts:
            message += f"Вы уже выбрали: {', '.join(map(lambda t: f'<b>{t}</b>', texts))}"
        await call.message.edit_text(message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            reply_markup=create_schedule_keyboard()
        )
        await state.update_data({"weekdays": weekdays, "texts": texts})
        await state.set_state(ScheduleState.weekdays)
    else:
        if not weekdays:
            await state.update_data({"weekdays": {0, 1, 2, 3, 4}})
        await call.message.edit_text(
            "Введите город, в котором живете (необходимо для настройки времени)"
        )
        await state.set_state(ScheduleState.location)


async def get_location(message: types.Message, state: FSMContext):
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.geocode(message.text)
    if location is not None:
        timezone = TimezoneFinder().timezone_at(
            lng=location.longitude, lat=location.latitude
        )

        await state.update_data({"timezone": timezone})
        await message.reply(str(location))
        await Telegram.send_message(
            message.from_user.id,
            "Введите время в формате HH:MM. В это время будут приходить уведомления"
        )
        await state.set_state(ScheduleState.time)
    else:
        msg = "Извините, такой город не найден(\n" \
              "Попробуйте проверить название города или введите другой"
        await message.answer(msg)
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


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
        await state.clear()
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите время от 00:00 до 23:59")
        await state.set_state(ScheduleState.time)
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_age(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert 0 <= value <= 100
        await state.update_data(age=value)
        await Telegram.send_message(message.from_user.id, "Введите рост 📏️ (в сантиметрах)")
        await state.set_state(SubscribeState.height)
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите целое число от 0 до 100")
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_height(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 50. <= value <= 300.
        await state.update_data(height=value)
        await Telegram.send_message(message.from_user.id, "Введите вес ⚖️ (в килограммах)")
        await state.set_state(SubscribeState.weight)
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите число от 50 до 300")
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_weight(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 20. <= value <= 220.
        await state.update_data(weight=value)
        await Telegram.send_message(
            message.from_user.id,
            "Выберите гендер 👨️/👩️/🚁️", reply_markup=create_gender_keyboard()
        )
        await state.set_state(SubscribeState.gender)
    except (ValueError, AssertionError) as error:
        await Telegram.send_message(message.from_user.id, "Введите число от 20 до 220")
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_gender(call: types.CallbackQuery, callback_data: Subscriber, state: FSMContext):
    data = await state.get_data()
    data["gender"] = callback_data.gender
    if await update_subscribe(call.from_user, data):
        await call.message.edit_text("Данные были успешно обновлены!")
    else:
        await call.message.edit_text("Что-то пошло не так")


async def get_activity(call: types.CallbackQuery, callback_data: Activity, state: FSMContext):
    data = await state.get_data()
    A = callback_data.value
    match data['gender']:
        case 'male':
            calories = int(((10 * data['weight']) + (6.25 * data['height']) - (5 * data['age'] + 5)) * A)
        case 'female':
            calories = int(((10 * data['weight']) + (6.25 * data['height']) - (5 * data['age'] - 161)) * A)
        case _:
            calories = None
    await call.message.edit_text(f'Дневная норма калорий: {calories}')


async def get_info(call: types.CallbackQuery, callback_data: Info, state: FSMContext):
    match callback_data.section:
        case '/my_health':
            info = info_my_health_message
        # case '/account':
        #     info = info_account_message
        case '/approaches':
            info = info_approaches_message
        case _:
            info = None
    await Telegram.send_message(call.from_user.id, info, parse_mode='HTML')


async def send_nutritions(call: types.CallbackQuery, state: FSMContext, direction: int = 1):
    nutritions = (await state.get_data()).get("nutritions", [])
    try:
        nutrition = nutritions.__next__(direction)
        await call.message.edit_text(nutrition.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            reply_markup=create_content_keyboard(nutrition)
        )
        await state.update_data({"nutritions": nutritions, "id": nutrition.id})
    except ValueError:
        await call.message.edit_text("Контента нет")
        return False
    else:
        return True


async def send_portions(call: types.CallbackQuery, state: FSMContext, direction: int = 1) -> bool:
    portions = (await state.get_data()).get("portions", [])
    try:
        portion = portions.__next__(direction)
        await call.message.edit_text(portion.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            reply_markup=create_move_keyboard()
        )
        await state.update_data({"portions": portions})
    except ValueError:
        await call.answer("Контента нет", show_alert=True)
        return False
    else:
        return True


async def get_next_nutrition(call: types.CallbackQuery, callback_data: Move, state: FSMContext):
    if callback_data.direction != 0:
        await send_nutritions(call, state, callback_data.direction)
        await state.set_state(NutritionState.next_nutrition)
    else:
        data = await state.get_data()
        await state.update_data({"portions": iter(Cycle(
            await get_portions({"nutrition_id": data.get("id", 0)})
        ))})
        if await send_portions(call, state, callback_data.direction):
            await state.set_state(NutritionState.next_portion)


async def get_next_portion(call: types.CallbackQuery, callback_data: Move, state: FSMContext):
    if callback_data.direction != 0:
        await send_portions(call, state, callback_data.direction)
        await state.set_state(NutritionState.next_portion)
    else:
        await send_nutritions(call, state, callback_data.direction)
        await state.set_state(NutritionState.next_nutrition)


async def send_programs(call: types.CallbackQuery, state: FSMContext, direction: int = 1) -> bool:
    programs = (await state.get_data()).get("programs", [])
    try:
        program = programs.__next__(direction)
        await call.message.edit_text(program.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            reply_markup=create_content_keyboard(program, training_program=program.id)
        )
        await state.update_data({"programs": programs, "id": program.id})
    except ValueError:
        await call.message.edit_text("Контента нет")
        return False
    else:
        return True


async def send_trainings(call: types.CallbackQuery, state: FSMContext, direction: int = 1) -> bool:
    trainings = (await state.get_data()).get("trainings", [])
    try:
        training = trainings.__next__(direction)
        await call.message.edit_text(training.message, parse_mode="HTML")
        await call.message.edit_reply_markup(
            reply_markup=create_move_keyboard()
        )
        await state.update_data({"trainings": trainings})
    except ValueError as error:
        await call.answer("Контента нет", show_alert=True)
        return False
    else:
        return True


async def get_program_filter(call: types.CallbackQuery, callback_data: Program, state: FSMContext):
    if callback_data.filtered:
        await call.message.edit_text("Введите уровень сложности (от 1.00 до 5.00)")
        await state.set_state(ProgramState.difficulty_value)
    else:
        await state.update_data({"programs": iter(Cycle(await get_programs()))})
        await send_programs(call, state)
        await state.set_state(ProgramState.next_program)


async def get_difficulty_value(message: types.Message, state: FSMContext):
    try:
        value = float(message.text)
        assert 1 <= value <= 5
        await state.update_data(difficulty=message.text)
        await Telegram.send_message(
            message.from_user.id,
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("difficulty", value)
        )
        await state.set_state(ProgramState.difficulty_op)
    except (AssertionError, ValueError) as valid_error:
        await message.answer("Введите десятичное число от 1 до 5")
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_difficulty_op(call: types.CallbackQuery, callback_data: Program, state: FSMContext):
    data = await state.get_data()
    await state.update_data(difficulty=callback_data.difficulty + data.get("difficulty"))
    await call.message.edit_text("Введите количество недель")
    await state.set_state(ProgramState.weeks_value)


async def get_weeks_value(message: types.Message, state: FSMContext):
    try:
        value = int(message.text)
        assert value > 0
        await state.update_data(weeks=message.text)
        await Telegram.send_message(
            message.from_user.id,
            "Введите операцию с числом",
            reply_markup=create_op_keyboard("weeks", value)
        )
        await state.set_state(ProgramState.weeks_op)
    except (AssertionError, ValueError) as valid_error:
        await message.answer("Введите число больше 0")
        await Telegram.delete_message(
            message.from_user.id, message.message_id - 1
        )
        await message.delete()


async def get_weeks_op(call: types.CallbackQuery, callback_data: Program, state: FSMContext):
    data = await state.get_data()
    data["weeks"] = callback_data.weeks + data.get("weeks")
    await state.update_data({"programs": iter(Cycle(await get_programs(data)))})
    await send_programs(call, state)
    await state.set_state(ProgramState.next_program)


async def get_next_program(call: types.CallbackQuery, callback_data: Move, state: FSMContext):
    if callback_data.direction != 0:
        await send_programs(call, state, callback_data.direction)
        await state.set_state(ProgramState.next_program)
    else:
        data = await state.get_data()
        await state.update_data({"trainings": iter(Cycle(
            await get_trainings({"program_id": data.get("id", 0)})
        ))})
        if await send_trainings(call, state, callback_data.direction):
            await state.set_state(ProgramState.next_training)


async def get_next_training(call: types.CallbackQuery, callback_data: Move, state: FSMContext):
    if callback_data.direction != 0:
        await send_trainings(call, state, callback_data.direction)
        await state.set_state(ProgramState.next_training)
    else:
        await send_programs(call, state, callback_data.direction)
        await state.set_state(ProgramState.next_program)
