from api import ApiClient, Telegram

from handlers import (
    start,
    account,
    subscribe,
    programs,
    nutritions,
    my_health,
    update_my_health,
    calculate_calories,
    buy_content,
    program,
    nutrition,
    schedule,
    approaches,
    disable_schedule
)
from notifications import scheduler
from states import (
    ProgramState,
    get_program_filter,
    get_difficulty_value,
    get_difficulty_op,
    get_weeks_value,
    get_weeks_op,
    get_next_program,
    get_next_training,
    SubscribeState,
    get_age,
    get_height,
    get_weight,
    get_gender,
    ScheduleState,
    get_weekdays,
    get_location,
    get_time,
    NutritionState,
    get_nutrition_filter,
    get_next_nutrition,
    get_next_portion,
    ApproachState,
    get_next_approach,
    CaloriesState,
    get_activity
)
from keyboards import (
    move,
    _filter,
    week_filter,
    difficulty_filter,
    gender_filter,
    schedule_filter,
    buy,
    program_filter,
    nutrition_filter,
    notification,
    activity_filter
)

from aiogram import Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage


storage = MemoryStorage()
dp = Dispatcher(Telegram, storage=storage)


@dp.callback_query_handler(text="quit_content", state="*")
async def delete_messages(call: types.CallbackQuery, state):
    await call.message.delete()
    msg = "Если я еще понадоблюсь, введите /start"
    await call.bot.send_message(call.from_user.id, msg)
    await state.finish()


dp.register_message_handler(start, commands=["start"], state="*")
dp.register_message_handler(programs, commands=["programs"], state="*")
dp.register_message_handler(subscribe, commands=["subscribe"], state="*")
dp.register_message_handler(account, commands=["account"], state="*")
dp.register_message_handler(nutritions, commands=["nutritions"], state="*")
dp.register_message_handler(my_health, commands=["my_health"], state="*")
dp.register_message_handler(approaches, commands=["approaches"], state="*")
dp.register_callback_query_handler(update_my_health, text="update_subscribe", state="*"),
dp.register_callback_query_handler(disable_schedule, text="quit_notification", state="*")
dp.register_callback_query_handler(calculate_calories, text="calculate_calories", state="*")
dp.register_callback_query_handler(buy_content, buy.filter(), state="*")
dp.register_callback_query_handler(program, program_filter.filter(), state="*")
dp.register_callback_query_handler(nutrition, nutrition_filter.filter(), state="*")
dp.register_callback_query_handler(schedule, notification.filter(), state="*")

"""Register Schedule states"""

dp.register_callback_query_handler(
    get_weekdays,
    schedule_filter.filter(),
    state=ScheduleState.weekdays
)
dp.register_message_handler(
    get_location,
    state=ScheduleState.location
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

dp.register_callback_query_handler(
    get_next_training,
    move.filter(),
    state=ProgramState.next_training
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

dp.register_callback_query_handler(
    get_next_portion,
    move.filter(),
    state=NutritionState.next_portion
)

"""Register Approach states"""

dp.register_callback_query_handler(
    get_next_approach,
    move.filter(),
    state=ApproachState.next_approach
)

"""Register update Subscriber states"""

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

'''Register CaloriesState'''
dp.register_callback_query_handler(
    get_activity,
    activity_filter.filter(),
    state=CaloriesState.activity
)

if __name__ == '__main__':
    scheduler.start()
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=ApiClient().update_cache,
        on_shutdown=ApiClient().clear_cache
    )
