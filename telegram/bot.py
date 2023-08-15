import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import text, command

from api import ApiClient, Telegram, create_anonymous_user

from handlers import (
    start,
    info,
    account,
    subscribe,
    programs,
    nutritions,
    my_health,
    update_my_health,
    calculate_calories,
    buy_content,
    program,
    schedule,
    approaches,
    disable_schedule,
    accrue_balance,
    unsubscribe
)
from middlewares import RegisterMiddleware, SubscribeMiddleware
from models import TelegramUser, Token
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
    get_next_nutrition,
    get_next_portion,
    ApproachState,
    get_next_approach,
    CaloriesState,
    get_activity,
    InfoState,
    get_info,
    PaymentState,
    get_balance
)
from keyboards import (
    COMMANDS,
    Move,
    ID,
    Content,
    Subscriber,
    Program,
    Schedule,
    Activity,
    Info
)

from aiogram import Dispatcher, types, Router, F

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

register_router = Router()
subscribe_router = Router()
register_router.message.middleware(RegisterMiddleware())
subscribe_router.message.middleware(SubscribeMiddleware())

register_router.callback_query.middleware(RegisterMiddleware())
subscribe_router.callback_query.middleware(SubscribeMiddleware())


@dp.callback_query(text.Text("quit"))
async def delete_messages(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    msg = "Если я еще понадоблюсь, введите /start"
    await Telegram.send_message(call.from_user.id, msg)
    await state.clear()


@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(pre_checkout_query.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user = await client.update_user(
            instance, token,
            cache=True, data={"balance": pre_checkout_query.total_amount / 100}
        )
        if isinstance(user, TelegramUser):
            await Telegram.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
        else:
            await Telegram.answer_pre_checkout_query(
                pre_checkout_query.id, error_message="Ошибка на сервере. Обратитесь в тех. поддержку", ok=False
            )


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    await Telegram.send_message(
        message.chat.id,
        "Вы успешно пополнили баланс на {total_amount} {currency}".format(
            total_amount=message.successful_payment.total_amount // 100,
            currency=message.successful_payment.currency
        )
    )


register_router.message.register(subscribe, text.Text(COMMANDS["subscribe"]))
register_router.message.register(unsubscribe, text.Text(COMMANDS["unsubscribe"]))
register_router.message.register(account, text.Text(COMMANDS["account"]))
register_router.callback_query.register(accrue_balance, text.Text("accrue_balance"))
dp.include_router(register_router)


subscribe_router.message.register(my_health, text.Text(COMMANDS["my_health"]))
subscribe_router.message.register(approaches, text.Text(COMMANDS["approaches"]))
subscribe_router.callback_query.register(calculate_calories, text.Text("calculate_calories"))
dp.include_router(subscribe_router)


dp.message.register(start, command.Command("start"))
dp.message.register(info, text.Text(COMMANDS["info"]))
dp.message.register(programs, text.Text(COMMANDS["programs"]))
dp.message.register(nutritions, text.Text(COMMANDS["nutritions"]))
dp.callback_query.register(update_my_health, text.Text("update_subscribe"))
dp.callback_query.register(disable_schedule, text.Text("disable_schedule"))
dp.callback_query.register(schedule, text.Text("set_schedule"))
dp.callback_query.register(buy_content, Content.filter())
dp.callback_query.register(program, ID.filter())

"""Register Schedule states"""

dp.callback_query.register(
    get_weekdays,
    Schedule.filter(),
    ScheduleState.weekdays
)
dp.message.register(
    get_location,
    ScheduleState.location
)
dp.message.register(
    get_time,
    ScheduleState.time
)

"""Register Training Program states"""

dp.callback_query.register(
    get_program_filter,
    Program.filter(),
    ProgramState.program_filter
)
dp.message.register(
    get_difficulty_value,
    ProgramState.difficulty_value
)
dp.callback_query.register(
    get_difficulty_op,
    Program.filter(),
    ProgramState.difficulty_op
)
dp.message.register(
    get_weeks_value,
    ProgramState.weeks_value
)
dp.callback_query.register(
    get_weeks_op,
    Program.filter(),
    ProgramState.weeks_op
)
dp.callback_query.register(
    get_next_program,
    Move.filter(),
    ProgramState.next_program
)

dp.callback_query.register(
    get_next_training,
    Move.filter(),
    ProgramState.next_training
)


"""Register Sport Nutrition states"""

dp.callback_query.register(
    get_next_nutrition,
    Move.filter(),
    NutritionState.next_nutrition
)

dp.callback_query.register(
    get_next_portion,
    Move.filter(),
    NutritionState.next_portion
)

"""Register Approach states"""

dp.callback_query.register(
    get_next_approach,
    Move.filter(),
    ApproachState.next_approach
)

"""Register update Subscriber states"""

dp.message.register(
    get_age,
    SubscribeState.age
)
dp.message.register(
    get_height,
    SubscribeState.height
)
dp.message.register(
    get_weight,
    SubscribeState.weight
)
dp.callback_query.register(
    get_gender,
    Subscriber.filter(),
    SubscribeState.gender
)

'''Register CaloriesState'''
dp.callback_query.register(
    get_activity,
    Activity.filter(),
    CaloriesState.activity
)

'''Register InfoState'''
dp.callback_query.register(
    get_info,
    Info.filter(),
    InfoState.info
)

"""Register Payment states"""

dp.message.register(
    get_balance,
    PaymentState.balance
)


async def main():
    scheduler.start()
    client = ApiClient()

    await client.update_cache(dp)
    await dp.start_polling(Telegram)
    await client.clear_cache(dp)


if __name__ == '__main__':
    asyncio.run(main())
