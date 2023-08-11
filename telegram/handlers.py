from aiogram import types
from aiogram.dispatcher import FSMContext

from api import (
    Telegram,
    ApiClient,
    create_anonymous_user,
    register_user,
    update_subscribe,
    get_program,
    get_nutrition,
    get_approaches,
    get_trainings
)
from keyboards import (
    start_keyboard,
    create_my_health_keyboard,
    filter_keyboard,
    start_schedule_keyboard,
    create_training_keyboard,
    activity_keyboard
)
from notifications import scheduler
from states import (
    ProgramState,
    NutritionState,
    SubscribeState,
    ScheduleState,
    ApproachState,
    CaloriesState,
    Cycle,
    Iterable
)
from models import (
    TelegramUser,
    Subscriber,
    Token,
    TrainingProgram,
    Nutrition,
)


async def start(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    user: TelegramUser = await register_user(client, instance)
    if user:
        msg: str = f"Привет {user.first_name} {user.last_name} 👋️\n\n" \
                   "Я <b>спорт-бот</b>, и я помогу тебе подобрать" \
                   "программу под твои интересы и физическую подготовку"
    else:
        msg: str = "Введите /my_health, чтобы посмотреть список доступных функций\n\n" \
                   "Если у вас возникли вопросы, обратитесь в <b>тех поддержку</b>"

    await message.reply(msg, reply_markup=start_keyboard, parse_mode="HTML")


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
    await Telegram.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=filter_keyboard
    )
    await ProgramState.program_filter.set()


async def nutritions(message: types.Message, state: FSMContext):
    await state.finish()
    await Telegram.send_message(
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
                    sport_nutrition=subscriber.sport_nutrition if subscriber.sport_nutrition else 0,
                    training_program=subscriber.training_program if subscriber.training_program else 0
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


async def calculate_calories(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        subscriber: Subscriber = (await client.get_user(instance, token, cache=True)).subscriber
        if subscriber.is_kfc_valid:
            await Telegram.send_message(call.from_user.id, "Какая у Вас дневная активность?", reply_markup=activity_keyboard)
            await state.update_data({
                    'age': subscriber.age,
                    'weight': subscriber.weight, 
                    'height': subscriber.height,
                    'gender': subscriber.gender 
                })
            await CaloriesState.activity.set()
        else:
            await Telegram.send_message(call.from_user.id, "Заполните данные своего профиля!")
    else:
        await Telegram.send_message(call.from_user.id, "Введите /start, чтобы зарегистрироваться")


async def buy_content(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    await state.finish()
    await call.answer("Внимание! Текущая программа будет заменена другой!", show_alert=True)
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
    await Telegram.send_message(
        call.message.chat.id,
        msg,
        reply_markup=start_schedule_keyboard
    )
    await state.update_data({"program_id": int(callback_data.get("program_id", 0))})
    await ScheduleState.weekdays.set()


async def disable_schedule(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    if scheduler.get_job(str(call.from_user.id)):
        scheduler.remove_job(str(call.from_user.id))
    await Telegram.send_message(
        call.from_user.id, "Уведомление успешно отменено!"
    )


async def approaches(message: types.Message, state: FSMContext):
    await state.finish()
    client = ApiClient()

    instance: TelegramUser = create_anonymous_user(message.chat)
    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        if subscriber := user.subscriber:
            if program_id := subscriber.training_program:
                trainings = iter(Iterable([
                    training.id for training in
                    await get_trainings({"program_id": program_id})
                ]))
                if trainings.loop:
                    instances = iter(
                        Cycle(await get_approaches(
                            message.from_user, {"training_id": next(trainings)}
                        ))
                    )
                    approach = next(instances)
                    await Telegram.send_message(
                        message.from_user.id, approach.message,
                        reply_markup=create_training_keyboard(), parse_mode="HTML"
                    )
                    await state.update_data({"trainings": trainings, "approaches": instances})
                    await ApproachState.next_approach.set()
                else:
                    await message.reply(
                        "Текущая программа тренировок находится в разработке. Обратитесь в тех поддержку."
                    )
            else:
                await message.reply(
                    "Программа не найдена. Подпишитесь на одну из доступных программ /programs"
                )
        else:
            await message.reply("Введите /subscribe, чтобы подписаться")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")
