from aiogram import types

from aiogram.utils.callback_data import CallbackData

from models import TrainingProgram, Nutrition


move = CallbackData("move", "direction")
program_filter = CallbackData("program", "id")
nutrition_filter = CallbackData("nutrition", "id")
buy = CallbackData("buy", "training_program", "sport_nutrition")
_filter = CallbackData("filter", "filter")
notification = CallbackData("notification", "program_id")
schedule_filter = CallbackData("schedule_filter", "filter", "weekday")
difficulty_filter = CallbackData("difficulty_filter", "difficulty")
week_filter = CallbackData("week_filter", "weeks")
gender_filter = CallbackData("gender", "gender")
activity_filter = CallbackData("activity", "activity")


op_filters = {
    "difficulty": difficulty_filter,
    "weeks": week_filter
}


def create_op_keyboard(param: str, value):
    if param in op_filters:
        return types.InlineKeyboardMarkup(3).add(
            types.InlineKeyboardButton("🔼️", callback_data=op_filters[param].new(
                **{param: ">"}
            )),
            types.InlineKeyboardButton(f"{value}", callback_data=op_filters[param].new(
                **{param: "="}
            )),
            types.InlineKeyboardButton("🔽️", callback_data=op_filters[param].new(
                **{param: "<"}
            ))
        )


def create_training_keyboard():
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Следующая тренировка", callback_data=move.new(
            direction=0
        ))
    )
    return keyboard.add(
        *move_buttons
    )


def create_move_keyboard():
    keyboard = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("Назад", callback_data=move.new(
            direction=0
        ))
    )
    return keyboard.add(
        *move_buttons
    )


def create_content_keyboard(content: TrainingProgram | Nutrition, **kwargs):
    look_up = types.InlineKeyboardButton(
        text="Подробнее...",
        callback_data=move.new(
            direction=0
        )
    )
    buy_it = types.InlineKeyboardButton(
        f"{content.price} руб 💰️" if content.price > 0. else "Получить бесплатно ✅️",
        callback_data=buy.new(
            sport_nutrition=kwargs.get("sport_nutrition", "none"),
            training_program=kwargs.get("training_program", "none")
        )
    )
    if kwargs.get("sport_nutrition") or kwargs.get("training_program"):
        keyboard = types.InlineKeyboardMarkup().add(buy_it, look_up)
    else:
        keyboard = types.InlineKeyboardMarkup().add(look_up)
    keyboard.add(
        *move_buttons
    )
    return keyboard


def create_my_health_keyboard(**kwargs):
    keyboard = types.InlineKeyboardMarkup(5).add(
        types.InlineKeyboardButton("Посмотреть программу", callback_data=program_filter.new(
            id=kwargs.get("training_program")
        )),
        types.InlineKeyboardButton("Отключить уведомление", callback_data="quit_notification")
    )
    keyboard.add(
        types.InlineKeyboardButton("Обновить данные", callback_data="update_subscribe"),
        types.InlineKeyboardButton("Запустить уведомление", callback_data=notification.new(
            program_id=kwargs.get("training_program")
        ))
    )
    keyboard.add(
        types.InlineKeyboardButton("Калькулятор калорий и БЖУ", callback_data="calculate_calories")
    )
    return keyboard


move_buttons = [
    types.InlineKeyboardButton("◀️", callback_data=move.new(direction=-1)),
    types.InlineKeyboardButton("Закрыть", callback_data='quit_content'),
    types.InlineKeyboardButton("▶️", callback_data=move.new(direction=1))
]


start_keyboard = types.ReplyKeyboardMarkup(3, one_time_keyboard=False).add(
    types.KeyboardButton(text="/subscribe Подписаться 🎁", callback_data="subscribe"),
    types.KeyboardButton(text="/my_health Мое здоровье 🫀️", callback_data="filter_programs"),
    types.KeyboardButton(text="/account Мои данные 📃️")
)

start_keyboard.add(
    types.KeyboardButton(text="/programs Программы тренировок 🎽"),
    types.KeyboardButton(text="/nutritions Спортивное питание 🥑"),
    types.KeyboardButton(text="/approaches Текущая тренировка ⏳")
)

filter_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton("Да", callback_data=_filter.new(
        filter=1
    )),
    types.InlineKeyboardButton("Нет", callback_data=_filter.new(
        filter=0
    )),
)

gender_keyboard = types.InlineKeyboardMarkup(3).add(
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

start_schedule_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton("Я сам все сделаю", callback_data=schedule_filter.new(
        filter=1,
        weekday="None"
    )),
    types.InlineKeyboardButton("Умолчание мне подходит", callback_data=schedule_filter.new(
        filter=0,
        weekday="None"
    )),
)

schedule_keyboard = types.InlineKeyboardMarkup(8).add(
    types.InlineKeyboardButton("пн", callback_data=schedule_filter.new(
        filter=1,
        weekday=0
    )),
    types.InlineKeyboardButton("вт", callback_data=schedule_filter.new(
        filter=1,
        weekday=1
    )),
    types.InlineKeyboardButton("ср", callback_data=schedule_filter.new(
        filter=1,
        weekday=2
    ))
)
schedule_keyboard.add(
    types.InlineKeyboardButton("чт", callback_data=schedule_filter.new(
        filter=1,
        weekday=3
    )),
    types.InlineKeyboardButton("пт", callback_data=schedule_filter.new(
        filter=1,
        weekday=4
    )),
    types.InlineKeyboardButton("сб", callback_data=schedule_filter.new(
        filter=1,
        weekday=5
    ))
)
schedule_keyboard.add(
    types.InlineKeyboardButton("вс", callback_data=schedule_filter.new(
        filter=1,
        weekday=6
    )),
    types.InlineKeyboardButton("хватит", callback_data=schedule_filter.new(
        filter=0,
        weekday="None"
    ))
)
activity_keyboard = types.InlineKeyboardMarkup(5).add(
    types.InlineKeyboardButton("Сидячий образ жизни", callback_data=activity_filter.new(
        activity=1.2
    )),
    types.InlineKeyboardButton("Умеренная активность", callback_data=activity_filter.new(
        activity=1.375
    )),
    types.InlineKeyboardButton("Средняя активность", callback_data=activity_filter.new(
        activity=1.55
    ))
)
activity_keyboard.add(
    types.InlineKeyboardButton("Интенсивные нагрузки", callback_data=activity_filter.new(
        activity=1.725
    )),
    types.InlineKeyboardButton("Активные занятия спортом", callback_data=activity_filter.new(
        activity=1.9
    ))
)