from api import ApiClient

from handlers import (
    send_welcome,
    get_account_info,
    subscribe,
    get_programs,
    get_nutritions,
    get_trainings, get_program, get_nutrition
)
from states import (
    program_filter_start,
    get_difficulty_value,
    get_difficulty_op,
    get_weeks_value,
    get_weeks_op,
    finish_program_filter,
    ProgramFilter,
)
from keyboards import (
    create_filter_keyboard,
    del_filter,
    program_filter,
    week_filter,
    difficulty_filter
)
from settings import config

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


tg = Bot(token=config.get("bot_token"))
storage = MemoryStorage()
dp = Dispatcher(tg, storage=storage)


@dp.callback_query_handler(del_filter.filter())
async def delete_messages(call: types.CallbackQuery, callback_data: dict):
    current_id, messages = int(call.message.message_id) - 1, int(callback_data.get("messages"))
    for _id in range(current_id, current_id-messages, -1):
        await tg.delete_message(call.message.chat.id, _id)
    await tg.delete_message(call.message.chat.id, current_id + 1)
    await tg.send_message(
        call.message.chat.id, "Список программ 🗒️",
        reply_markup=create_filter_keyboard()
    )


dp.register_message_handler(send_welcome, commands=["start"])
dp.register_message_handler(get_account_info, commands=["account"])
dp.register_callback_query_handler(subscribe, text="subscribe")
dp.register_message_handler(get_programs, commands=["programs"])
dp.register_message_handler(get_nutritions, commands=["nutritions"])
dp.register_message_handler(get_trainings, commands=["trainings"])
dp.register_callback_query_handler(get_program, text="program")
dp.register_callback_query_handler(get_nutrition, text="nutrition")
dp.register_callback_query_handler(program_filter_start, text="filter_programs"),
dp.register_callback_query_handler(
    get_difficulty_value,
    program_filter.filter(),
    state=ProgramFilter.difficulty_value
)
dp.register_message_handler(get_difficulty_op, state=ProgramFilter.difficulty_op)
dp.register_callback_query_handler(
    get_weeks_value,
    difficulty_filter.filter(),
    state=ProgramFilter.weeks_value)
dp.register_message_handler(get_weeks_op, state=ProgramFilter.weeks_op)
dp.register_callback_query_handler(
    finish_program_filter,
    week_filter.filter(),
    state=ProgramFilter.finish_filter)


if __name__ == '__main__':
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=ApiClient().update_cache,
        on_shutdown=ApiClient().clear_cache
    )
