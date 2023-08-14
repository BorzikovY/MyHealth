from aiogram import types
from aiogram.fsm.context import FSMContext

from api import (
    Telegram,
    ApiClient,
    create_anonymous_user,
    register_user,
    update_subscribe,
    get_program,
    get_approaches,
    get_trainings, 
    get_nutritions
)
from keyboards import (
    start_keyboard,
    create_my_health_keyboard,
    start_callback_keyboard,
    create_training_keyboard,
    balance_keyboard, 
    ID, 
    Program, 
    Schedule, 
    Content, 
    create_content_keyboard,
    activity_keyboard,
    info_keyboard
)
from notifications import scheduler
from states import (
    ProgramState,
    NutritionState,
    SubscribeState,
    ScheduleState,
    ApproachState,
    CaloriesState,
    InfoState,
    Cycle,
    Iterable
)
from models import (
    TelegramUser,
    Subscriber,
    Token,
    TrainingProgram
)


async def start(message: types.Message, state: FSMContext):
    await state.clear()
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


async def account(message: types.Message, client: ApiClient, args):
    user: TelegramUser = await client.get_user(*args, cache=True)
    await message.reply(user.message, reply_markup=balance_keyboard, parse_mode="HTML")


async def info(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await Telegram.send_message(
        call.from_user.id,
        "О каком разделе вы хотите посмотреть информацию?",
        reply_markup=info_keyboard
        )
    await state.set_state(InfoState.info)


async def subscribe(message: types.Message, state: FSMContext):
    await state.clear()
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
    await state.clear()
    await Telegram.send_message(
        message.from_user.id,
        "Включить в подборку фильтрацию?",
        reply_markup=start_callback_keyboard(Program, ["Да", "Нет"])
    )
    await state.set_state(ProgramState.program_filter)


async def nutritions(message: types.Message, state: FSMContext):
    await state.clear()
    instances = iter(Cycle(await get_nutritions()))
    nutrition = instances.__next__()

    await Telegram.send_message(
        message.from_user.id,
        nutrition.message, parse_mode="HTML",
        reply_markup=create_content_keyboard(nutrition)
    )

    await state.update_data({"nutritions": instances, "id": nutrition.id})
    await state.set_state(NutritionState.next_nutrition)


async def my_health(message: types.Message, state: FSMContext):
    await state.clear()
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
                    id=subscriber.training_program
                )
            )
        else:
            await message.reply("Сначала подпишитесь")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")


async def update_my_health(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Введите возраст 👶️-🧓️",
    )
    await state.set_state(SubscribeState.age)


async def calculate_calories(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(call.from_user)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        subscriber: Subscriber = (await client.get_user(instance, token, cache=True)).subscriber
        if subscriber.is_kfc_valid:
            await Telegram.send_message(
                call.from_user.id,
                "Какая у Вас дневная активность?", reply_markup=activity_keyboard
            )
            await state.update_data({
                    'age': subscriber.age,
                    'weight': subscriber.weight,
                    'height': subscriber.height,
                    'gender': subscriber.gender
                })
            await state.set_state(CaloriesState.activity)
        else:
            await Telegram.send_message(call.from_user.id, "Заполните данные своего профиля!")
    else:
        await Telegram.send_message(call.from_user.id, "Введите /start, чтобы зарегистрироваться")


async def buy_content(call: types.CallbackQuery, callback_data: Content, state: FSMContext):
    await state.clear()
    await call.answer("Внимание! Текущая программа будет заменена другой!", show_alert=True)
    data = {
        "training_program": callback_data.training_program,
        "sport_nutrition": callback_data.sport_nutrition
    }
    if await update_subscribe(call.from_user, data):
        await call.message.edit_text("Вы успешно преобрели продукт!")
    else:
        await call.message.edit_text("Продукт не был преобретен. Проверьте баланс или обратитесь в тех поддержку.")


async def program(call: types.CallbackQuery, callback_data: ID, state: FSMContext):
    await state.clear()
    instance = await get_program(call.from_user, {"id": callback_data.id})
    if isinstance(instance, TrainingProgram):
        await call.message.answer(instance.message, parse_mode="HTML")
    else:
        msg = "Вы еще не преобрели тренировочную программу\n\n" \
              "Нажмите на кнопку в меню, чтобы вывести список программ"
        await call.message.answer(msg)


async def schedule(call: types.CallbackQuery, callback_data: ID, state: FSMContext):
    await state.clear()
    msg = "Сконфигурируйте расписание самостоятельно или\n " \
          "используйте параметры по умолчанию\n\n" \
          "(уведомления будут приходить с понедельника по пятницу)"
    await Telegram.send_message(
        call.message.chat.id,
        msg,
        reply_markup=start_callback_keyboard(Schedule, ["Я сделаю все сам", "По умолчанию"])
    )
    await state.update_data({"program_id": callback_data.id})
    await state.set_state(ScheduleState.weekdays)


async def disable_schedule(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if scheduler.get_job(str(call.from_user.id)):
        scheduler.remove_job(str(call.from_user.id))
    await Telegram.send_message(
        call.from_user.id, "Уведомление успешно отменено!"
    )


async def approaches(message: types.Message, state: FSMContext):
    await state.clear()
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
                    await state.set_state(ApproachState.next_approach)
                else:
                    await message.reply(
                        "Текущая программа тренировок находится в разработке. Обратитесь в тех поддержку."
                    )
            else:
                await message.reply(
                    "Программа не найдена. Подпишитесь на одну из доступных программ"
                )
        else:
            await message.reply("Введите /subscribe, чтобы подписаться")
    else:
        await message.reply("Введите /start, чтобы зарегистрироваться")
