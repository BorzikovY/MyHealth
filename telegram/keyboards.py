from aiogram import types

from aiogram.utils.callback_data import CallbackData


del_filter = CallbackData("delete", "messages")
program = CallbackData("program", "id")
nutrition = CallbackData("nutrition", "id")
update_subscribe = CallbackData("subscribe", "training_program", "sport_nutrition")
program_filter = CallbackData("program_filter", "filter")
schedule_filter = CallbackData("schedule_filter", "filter", "weekday")
difficulty_filter = CallbackData("difficulty_filter", "difficulty")
week_filter = CallbackData("week_filter", "weeks")
gender_filter = CallbackData("gender", "gender")


op_filters = {
    "difficulty": difficulty_filter,
    "weeks": week_filter
}


def create_filter_keyboard(callback_data: str = None, messages=None):
    buttons = []
    if callback_data:
        buttons.append(
            types.InlineKeyboardButton(text="Обновить запрос", callback_data=callback_data)
        )
    if messages:
        buttons.append(
            types.InlineKeyboardButton("Удалить все", callback_data=del_filter.new(
                messages=messages
            ))
        )
    return types.InlineKeyboardMarkup(2).add(*buttons)


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


start_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton(text="Подписаться 🎁", callback_data="subscribe"),
    types.InlineKeyboardButton(text="Я только посмотреть 😏️", callback_data="filter_programs")
)

start_program_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton("Да", callback_data=program_filter.new(
        filter=1
    )),
    types.InlineKeyboardButton("Нет", callback_data=program_filter.new(
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
