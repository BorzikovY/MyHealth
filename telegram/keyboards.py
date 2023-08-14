from typing import Optional, List

from aiogram.types import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from models import TrainingProgram, Nutrition


class Move(CallbackData, prefix="move"):
    direction: int = 1


class ID(CallbackData, prefix="id"):
    id: Optional[int] = None


class Content(CallbackData, prefix="content"):
    training_program: Optional[int] = None
    sport_nutrition: Optional[int] = None


class Schedule(CallbackData, prefix="schedule"):
    filtered: bool = True
    text: Optional[str] = None
    weekday: Optional[int] = None


class Program(CallbackData, prefix="content"):
    filtered: bool = True
    difficulty: Optional[str] = None
    weeks: Optional[str] = None


class Activity(CallbackData, prefix="activity"):
    value: float


class Info(CallbackData, prefix="info"):
    section: str


class Subscriber(CallbackData, prefix="subscriber"):
    gender: str = "helicopter"


def move_buttons() -> List[InlineKeyboardButton]:
    return [
        {"text": "◀️", "callback_data": Move(direction=-1)},
        {"text": "Закрыть", "callback_data": 'quit'},
        {"text": "▶️", "callback_data": Move(direction=1)}
    ]


def create_op_keyboard(param: str, value):
    keyboard_builder = InlineKeyboardBuilder()
    if param in ["difficulty", "weeks"]:
        keyboard_builder.button(text="🔼️", callback_data=Program(**{param: ">"}))
        keyboard_builder.button(text=f"{value}", callback_data=Program(**{param: "="}))
        keyboard_builder.button(text="🔽️", callback_data=Program(**{param: "<"}))
    keyboard_builder.adjust(3)
    return keyboard_builder.as_markup()


def create_training_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Следующая тренировка", callback_data=Move(direction=0))
    for button in move_buttons():
        keyboard_builder.button(**button)
    keyboard_builder.adjust(1, 3)
    return keyboard_builder.as_markup()


def create_move_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Назад", callback_data=Move(direction=0))
    for button in move_buttons():
        keyboard_builder.button(**button)
    keyboard_builder.adjust(1, 3)
    return keyboard_builder.as_markup()


def create_content_keyboard(content: TrainingProgram | Nutrition, **kwargs):
    keyboard_builder = InlineKeyboardBuilder()

    first_line = 1
    keyboard_builder.button(
        text="Подробнее...",
        callback_data=Move(
            direction=0
        )
    )
    if kwargs.get("sport_nutrition") or kwargs.get("training_program"):
        first_line += 1
        keyboard_builder.button(
            text=f"{content.price} руб 💰️" if content.price > 0. else "Получить бесплатно ✅️",
            callback_data=Content(
                sport_nutrition=kwargs.get("sport_nutrition"),
                training_program=kwargs.get("training_program")
            )
        )
    for button in move_buttons():
        keyboard_builder.button(**button)
    keyboard_builder.adjust(first_line, 3)
    return keyboard_builder.as_markup()


def create_my_health_keyboard(enable=True, **kwargs):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(
        text="Посмотреть программу", callback_data=ID(**kwargs)
    )
    keyboard_builder.button(text="Заполнить данные", callback_data="update_subscribe")
    if enable:
        keyboard_builder.button(text="Запустить уведомление", callback_data="set_schedule")
    else:
        keyboard_builder.button(text="Отключить уведомление", callback_data="disable_schedule")

    keyboard_builder.button(text="Калькулятор калорий и БЖУ", callback_data="calculate_calories")

    keyboard_builder.adjust(2, 2)
    return keyboard_builder.as_markup()


def start_callback_keyboard(filter_class: [Program | Schedule], texts: List[str]):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text=texts[0], callback_data=filter_class(filtered=True))
    keyboard_builder.button(text=texts[1], callback_data=filter_class(filtered=False))

    keyboard_builder.adjust(2)
    return keyboard_builder.as_markup()


def create_gender_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="мужской", callback_data=Subscriber(gender="male"))
    keyboard_builder.button(text="женский", callback_data=Subscriber(gender="female"))
    keyboard_builder.button(text="другой", callback_data=Subscriber(gender="helicopter"))

    keyboard_builder.adjust(3)
    return keyboard_builder.as_markup()


def create_schedule_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="пн", callback_data=Schedule(weekday=0, text="пн"))
    keyboard_builder.button(text="вт", callback_data=Schedule(weekday=1, text="вт"))
    keyboard_builder.button(text="ср", callback_data=Schedule(weekday=2, text="ср"))
    keyboard_builder.button(text="чт", callback_data=Schedule(weekday=3, text="чт"))
    keyboard_builder.button(text="пт", callback_data=Schedule(weekday=4, text="пт"))
    keyboard_builder.button(text="сб", callback_data=Schedule(weekday=5, text="сб"))
    keyboard_builder.button(text="вс", callback_data=Schedule(weekday=6, text="вс"))
    keyboard_builder.button(text="Готово!", callback_data=Schedule(filtered=False))

    keyboard_builder.adjust(3, 3, 2)
    return keyboard_builder.as_markup()


def create_activity_keyboard():
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Сидячий образ жизни", callback_data=Activity(value=1.2))
    keyboard_builder.button(text="Умеренная активность", callback_data=Activity(value=1.375))
    keyboard_builder.button(text="Средняя активность", callback_data=Activity(value=1.55))
    keyboard_builder.button(text="Интенсивные нагрузки", callback_data=Activity(value=1.725))
    keyboard_builder.button(text="Активные занятия спортом", callback_data=Activity(value=1.9))

    keyboard_builder.adjust(2, 2, 1)
    return keyboard_builder.as_markup()


def create_info_keyboard():
    keyboard_builder = InlineKeyboardBuilder()

    keyboard_builder.button(text="Мое здоровье 🫀️", callback_data=Info(section='/my_health'))
    keyboard_builder.button(text="Мои данные 📃️", callback_data=Info(section='/account'))
    keyboard_builder.button(text="Текущая тренировка ⏳", callback_data=Info(section='/approaches'))

    keyboard_builder.adjust(1, 1, 1)
    return keyboard_builder.as_markup()


COMMANDS = {
    "subscribe": "Подписаться 🎁",
    "my_health": "Мое здоровье 🫀️",
    "account": "Мои данные 📃️",
    "info": "Информация о разделах ❓️",
    "programs": "Программы тренировок 🎽",
    "nutritions": "Спортивное питание 🥑",
    "approaches": "Текущая тренировка ⏳"
}


start_keyboard = ReplyKeyboardMarkup(one_time_keyboard=False, keyboard=[
    [
        KeyboardButton(text=COMMANDS["subscribe"]),
        KeyboardButton(text=COMMANDS["my_health"]),
        KeyboardButton(text=COMMANDS["account"])
    ],
    [
        KeyboardButton(text=COMMANDS["info"])
    ],
    [
        KeyboardButton(text=COMMANDS["programs"]),
        KeyboardButton(text=COMMANDS["nutritions"]),
        KeyboardButton(text=COMMANDS["approaches"])
    ]
])

balance_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="Пополнить баланс 🤑", callback_data="payment")
]])