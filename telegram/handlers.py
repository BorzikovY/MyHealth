from aiogram import types
from aiogram.dispatcher import FSMContext

from api import (
    ApiClient,
    create_anonymous_user,
    register_user,
    update_subscribe,
    get_program,
    get_nutrition, get_approaches
)
from keyboards import (
    start_keyboard,
    create_my_health_keyboard,
    filter_keyboard,
    start_schedule_keyboard, move_buttons
)
from notifications import scheduler
from states import (
    ProgramState,
    NutritionState,
    SubscribeState,
    ScheduleState,
    ApproachState, Cycle
)
from models import (
    TelegramUser,
    Token,
    TrainingProgram,
    Nutrition,
)


async def start(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    await register_user(client, instance)
    msg: str = "Привет 👋️ Я *спорт\-бот*, и я помогу тебе подобрать\n" \
               "программу под твои интересы и физическую подготовку"

    await message.reply(msg, reply_markup=start_keyboard, parse_mode="MarkdownV2")


async def account(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        msg = user.message
    else:
        msg = "Введите /start, чтобы зарегистрироваться"

    await message.reply(msg, parse_mode="HTML")


async def subscribe(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        await client.create_subscriber(instance, token)
        msg: str = f"Вы подписаны!"
    else:
        msg = "Введите /start, чтобы зарегистрироваться"
    await message.answer(msg)


async def programs(message: types.Message, state: FSMContext):
    await state.finish()
    await message.bot.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=filter_keyboard
    )
    await ProgramState.program_filter.set()


async def nutritions(message: types.Message, state: FSMContext):
    await state.finish()
    await message.bot.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=filter_keyboard
    )
    await NutritionState.nutrition_filter.set()


async def my_health(message: types.Message):
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.chat)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        if subscriber := user.subscriber:
            await message.reply(
                subscriber.message,
                parse_mode="HTML",
                reply_markup=create_my_health_keyboard(
                    sport_nutrition=subscriber.sport_nutrition,
                    training_program=subscriber.training_program
                )
            )
        else:
            await message.reply("Введите /subscribe, чтобы подписаться")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")


async def update_my_health(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(
        "Введите возраст 👶️-🧓️",
    )
    await SubscribeState.age.set()


async def buy_content(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    data = {key: value for key, value in callback_data.items() if value.isnumeric()}
    if await update_subscribe(call.from_user, data):
        await call.message.edit_text("Вы успешно преобрели продукт!")
    else:
        await call.message.edit_text("Продукт не был преобретен. Проверьте баланс или обратитесь в тех поддержку.")


async def program(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    instance = await get_program(call.from_user, {"id": int(callback_data.get("id", 0))})
    if isinstance(instance, TrainingProgram):
        await call.message.answer(instance.message, parse_mode="HTML")
    else:
        msg = "Вы еще не преобрели тренировочную программу\n\n" \
              "Введите /programs, чтобы просмотреть список доступных программ"
        await call.message.answer(msg)


async def nutrition(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    instance = await get_nutrition(call.from_user, {"id": int(callback_data.get("id", 0))})
    if isinstance(instance, Nutrition):
        await call.message.answer(instance.message, parse_mode="HTML")
    else:
        msg = "Вы еще не преобрели подписку на спортивное питание\n\n" \
              "Введите /nutritions, чтобы просмотреть список спортивного питания"
        await call.message.answer(msg)


async def schedule(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    msg = "Сконфигурируйте расписание самостоятельно или\n " \
          "используйте параметры по умолчанию\n\n" \
          "(уведомления будут приходить с понедельника по пятницу)"
    await call.bot.send_message(
        call.message.chat.id,
        msg,
        reply_markup=start_schedule_keyboard
    )
    await state.update_data({"program_id": int(callback_data.get("program_id", 0))})
    await ScheduleState.weekdays.set()


async def approaches(message: types.Message, state: FSMContext):
    await state.finish()
    job = scheduler.get_job(str(message.from_user.id))
    if trainings := job.kwargs.get("trainings"):
        instances = iter(Cycle(await get_approaches(
            message.from_user,
            {"training_id": trainings.current}
        )))
        if instances.loop:
            approach = instances.__next__(0)
            await message.delete()
            await message.bot.send_message(
                message.from_user.id, approach.message,
                reply_markup=types.InlineKeyboardMarkup().add(
                    *move_buttons
                ), parse_mode="HTML"
            )
            await state.update_data({"approaches": instances})
            await ApproachState.next_approach.set()
        else:
            await message.reply(
                "Тренировка находится в разработке. Обратитесь в тех поддержку."
            )
    else:
        await message.reply(
            "Уведомление не найдено. Установите уведомление о начале тренировки в меню /my_health"
        )


