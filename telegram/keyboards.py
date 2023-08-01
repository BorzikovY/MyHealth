from aiogram import types

from aiogram.utils.callback_data import CallbackData


del_filter = CallbackData("delete", "messages")
program = CallbackData("program", "id")
nutrition = CallbackData("nutrition", "id")
update_subscribe = CallbackData("subscribe", "training_program", "sport_nutrition")
program_filter = CallbackData("program_filter", "filter")
difficulty_filter = CallbackData("difficulty_filter", "difficulty")
week_filter = CallbackData("week_filter", "weeks")
gender_filter = CallbackData("gender", "gender")


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


start_keyboard = types.InlineKeyboardMarkup(2).add(
    types.InlineKeyboardButton(text="Подписаться 🎁", callback_data="subscribe"),
    types.InlineKeyboardButton(text="Я только посмотреть 😏️", callback_data="filter_programs")
)
