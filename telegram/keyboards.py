from aiogram import types

from aiogram.utils.callback_data import CallbackData


del_filter = CallbackData("delete", "messages")
program_filter = CallbackData("program_filter", "filter")
difficulty_filter = CallbackData("difficulty_filter", "difficulty")
week_filter = CallbackData("week_filter", "weeks")


def create_filter_keyboard(messages=None):
    buttons = [types.InlineKeyboardButton(text="Обновить запрос", callback_data="filter_programs")]
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
