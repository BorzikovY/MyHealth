from aiogram import types

from aiogram.utils.callback_data import CallbackData

from models import TrainingProgram, Nutrition


move = CallbackData("move", "direction")
program = CallbackData("program", "id")
nutrition = CallbackData("nutrition", "id")
buy = CallbackData("buy", "training_program", "sport_nutrition")
_filter = CallbackData("filter", "filter")
schedule_filter = CallbackData("schedule_filter", "filter", "weekday")
difficulty_filter = CallbackData("difficulty_filter", "difficulty")
week_filter = CallbackData("week_filter", "weeks")
gender_filter = CallbackData("gender", "gender")


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


def create_content_keyboard(content: TrainingProgram | Nutrition, **kwargs):
    if kwargs.get("sport_nutrition"):
        filter_obj = nutrition
    elif kwargs.get("training_program"):
        filter_obj = program
    else:
        raise ValueError("You must provide either sport_nutrition or training_program")
    keyboard = types.InlineKeyboardMarkup(4).add(
        types.InlineKeyboardButton(
            f"{content.price} руб 💰️" if content.price > 0. else "Получить бесплатно ✅️",
            callback_data=buy.new(
                sport_nutrition=kwargs.get("sport_nutrition", "none"),
                training_program=kwargs.get("training_program", "none")
            )
        ),
        types.InlineKeyboardButton(
            text="Подробнее...",
            callback_data=filter_obj.new(
                id=content.id
            )
        )
    )
    keyboard.add(
        types.InlineKeyboardButton("◀️", callback_data=move.new(direction=-1)),
        types.InlineKeyboardButton("Закрыть", callback_data='quit_programs'),
        types.InlineKeyboardButton("▶️", callback_data=move.new(direction=1))
    )
    return keyboard


def create_my_health_keyboard(**kwargs):
    keyboard = types.InlineKeyboardMarkup(4).add(
        types.InlineKeyboardButton("Посмотреть программу", callback_data=program.new(
            id=kwargs.get("training_program")
        )),
        types.InlineKeyboardButton("Посмотреть питание", callback_data=nutrition.new(
            id=kwargs.get("sport_nutrition")
        ))
    )
    keyboard.add(
        types.InlineKeyboardButton("Обновить данные", callback_data="update_subscribe"),
        types.InlineKeyboardButton("Запустить уведомление", callback_data="filter_schedule")
    )
    return keyboard


start_keyboard = types.ReplyKeyboardMarkup(3, one_time_keyboard=False).add(
    types.KeyboardButton(text="/subscribe Подписаться 🎁", callback_data="subscribe"),
    types.KeyboardButton(text="/my_health Мое здоровье 🫀️", callback_data="filter_programs"),
    types.KeyboardButton(text="/account Мои данные 📃️")
)

start_keyboard.add(
    types.KeyboardButton(text="/programs Тренировочные программы 🎽"),
    types.KeyboardButton(text="/nutritions Спортивное питание 🥑"),
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
