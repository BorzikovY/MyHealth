from api import ApiClient

from handlers import (
    start,
    account,
    subscribe,
    programs,
    nutritions,
    my_health,
    update_subscribe
)
from states import (
    ProgramState,
    get_program_filter,
    get_difficulty_value,
    get_difficulty_op,
    get_weeks_value,
    get_weeks_op,
    get_next_program,
    SubscribeState,
    get_age,
    get_height,
    get_weight,
    get_gender,
    ScheduleState,
    start_schedule_filter,
    get_weekdays,
    get_time,
    NutritionState,
    get_nutrition_filter,
    get_next_nutrition
)
from keyboards import (
    move,
    _filter,
    week_filter,
    difficulty_filter,
    gender_filter,
    schedule_filter
)
from settings import config

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


tg = Bot(token=config.get("bot_token"))
storage = MemoryStorage()
dp = Dispatcher(tg, storage=storage)


@dp.callback_query_handler(text="quit_programs", state="*")
async def delete_messages(call: types.CallbackQuery, state):
    await call.message.delete()
    msg = "Надеюсь, что вы нашли то, что искали"
    await call.bot.send_message(call.from_user.id, msg)
    await state.finish()


dp.register_message_handler(start, commands=["start"], state="*")
dp.register_message_handler(programs, commands=["programs"], state="*")
dp.register_message_handler(subscribe, commands=["subscribe"], state="*")
dp.register_message_handler(account, commands=["account"], state="*")
dp.register_message_handler(nutritions, commands=["nutritions"], state="*")
dp.register_message_handler(my_health, commands=["my_health"], state="*")
dp.register_callback_query_handler(update_subscribe, text="update_subscribe", state="*")
dp.register_callback_query_handler(start_schedule_filter, text="filter_schedule")
dp.register_callback_query_handler(
    get_weekdays,
    schedule_filter.filter(),
    state=ScheduleState.weekdays
)
dp.register_message_handler(
    get_time,
    state=ScheduleState.time
)

"""Register Training Program states"""

dp.register_callback_query_handler(
    get_program_filter,
    _filter.filter(),
    state=ProgramState.program_filter
)
dp.register_message_handler(
    get_difficulty_value,
    state=ProgramState.difficulty_value
)
dp.register_callback_query_handler(
    get_difficulty_op,
    difficulty_filter.filter(),
    state=ProgramState.difficulty_op
)
dp.register_message_handler(
    get_weeks_value,
    state=ProgramState.weeks_value
)
dp.register_callback_query_handler(
    get_weeks_op,
    week_filter.filter(),
    state=ProgramState.weeks_op
)
dp.register_callback_query_handler(
    get_next_program,
    move.filter(),
    state=ProgramState.next_program
)

"""Register Sport Nutrition states"""

dp.register_callback_query_handler(
    get_nutrition_filter,
    _filter.filter(),
    state=NutritionState.nutrition_filter
)
dp.register_callback_query_handler(
    get_next_nutrition,
    move.filter(),
    state=NutritionState.next_nutrition
)

"""Update Subscriber info"""

dp.register_message_handler(
    get_age,
    state=SubscribeState.age
)
dp.register_message_handler(
    get_height,
    state=SubscribeState.height
)
dp.register_message_handler(
    get_weight,
    state=SubscribeState.weight
)
dp.register_callback_query_handler(
    get_gender,
    gender_filter.filter(),
    state=SubscribeState.gender
)


if __name__ == '__main__':
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=ApiClient().update_cache,
        on_shutdown=ApiClient().clear_cache
    )
