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
    get_nutritions,
    get_programs
)
from keyboards import (
    start_keyboard,
    create_my_health_keyboard,
    start_callback_keyboard,
    create_training_keyboard,
    balance_keyboard,
    create_content_keyboard,
    create_info_keyboard,
    create_activity_keyboard,
    ID,
    Schedule,
    Content, COMMANDS,
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
    Iterable,
    PaymentState
)
from models import (
    TelegramUser,
    Subscriber,
    TrainingProgram, Token
)


async def start(message: types.Message, state: FSMContext):
    await state.clear()
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message.from_user)

    token: Token = await client.get_token(instance)
    if not isinstance(token, Token):
        user: TelegramUser = await register_user(client, instance)
        msg: str = f"Привет {user.first_name} {user.last_name} 👋️\n\n" \
                   "Я <b>спорт-бот</b>, и я помогу тебе подобрать" \
                   "программу под твои интересы и физическую подготовку"
    else:
        user: TelegramUser = await client.get_user(instance, token, cache=True)
        if user.subscriber is not None:
            start_keyboard.keyboard[0][0].text = COMMANDS["unsubscribe"]
        else:
            start_keyboard.keyboard[0][0].text = COMMANDS["subscribe"]
        msg: str = "Нажмите на кнопку <b>Моё здоровье 🫀️</b>, чтобы настроить оповещения " \
                   "о начале тренировок или посмотреть информацию о здоровье\n\n" \
                   "Если у вас возникли вопросы, обратитесь в <b>тех поддержку</b>"

    await message.reply(msg, reply_markup=start_keyboard, parse_mode="HTML")


async def account(message: types.Message, state: FSMContext, client: ApiClient, args):
    await state.clear()
    user: TelegramUser = await client.get_user(*args, cache=True)
    await message.reply(user.message, reply_markup=balance_keyboard, parse_mode="HTML")


async def info(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await Telegram.send_message(
        call.from_user.id,
        "О каком разделе вы хотите посмотреть информацию?",
        reply_markup=create_info_keyboard()
        )
    await state.set_state(InfoState.info)


async def subscribe(message: types.Message, state: FSMContext, client: ApiClient, args):
    await state.clear()
    await client.create_subscriber(*args)
    msg = "Вы подписаны! Нажмите в меню <b>Мое здоровье 🫀️</b>, " \
          "чтобы заполнить данные о ваших физических характеристиках"
    await message.answer(msg, parse_mode="HTML")


async def unsubscribe(message: types.Message, state: FSMContext, client: ApiClient, args):
    await state.clear()
    await client.delete_subscriber(*args)
    msg = "Вы отписались! Все данные о вашем здоровье удалены(\n\n" \
          "Если вы случайно нажали на кнопку <b>Отписаться 🚫</b>, " \
          "обратитесь в тех. поддержку. Вам помогут востановить данные."
    await message.answer(msg, parse_mode="HTML")


async def programs(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        instances = iter(Cycle(await get_programs()))
        instance = instances.__next__()
        await Telegram.send_message(
            message.from_user.id,
            instance.message, parse_mode="HTML",
            reply_markup=create_content_keyboard(instance, training_program=instance.id)
        )
        await state.update_data({"programs": instances, "id": instance.id})
        await state.set_state(ProgramState.next_program)
    except ValueError:
        await message.reply("Контента нет")


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


async def my_health(message: types.Message, state: FSMContext, subscriber: Subscriber):
    await state.clear()
    await message.reply(
        subscriber.message,
        parse_mode="HTML",
        reply_markup=create_my_health_keyboard(
            scheduler.get_job(str(message.from_user.id)) is None,
            id=subscriber.training_program
        )
    )


async def update_my_health(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Введите возраст 👶️-🧓️",
    )
    await state.set_state(SubscribeState.age)


async def calculate_calories(call: types.CallbackQuery, state: FSMContext, subscriber: Subscriber):
    await state.clear()
    if subscriber.is_kfc_valid:
        await Telegram.send_message(
            call.from_user.id,
            "Какая у Вас дневная активность?", reply_markup=create_activity_keyboard()
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


async def buy_content(call: types.CallbackQuery, callback_data: Content, state: FSMContext):
    await state.clear()
    data = {
        "training_program": callback_data.training_program,
        "sport_nutrition": callback_data.sport_nutrition
    }
    if await update_subscribe(call.from_user, data):
        await call.message.edit_text("Вы успешно преобрели продукт!")
    else:
        await call.message.edit_text("Продукт не был преобретен. Проверьте баланс или обратитесь в тех поддержку.")


async def accrue_balance(call: types.CallbackQuery, state: FSMContext, args):
    await state.clear()
    await call.message.edit_text("Введите сумму пополнения (в рублях)")
    await state.set_state(PaymentState.balance)


async def program(call: types.CallbackQuery, callback_data: ID, state: FSMContext):
    await state.clear()
    instance = await get_program(call.from_user, {"id": callback_data.id})
    if isinstance(instance, TrainingProgram):
        await call.message.answer(instance.message, parse_mode="HTML")
    else:
        msg = "Вы еще не преобрели тренировочную программу\n\n" \
              "Нажмите на кнопку в меню, чтобы вывести список программ"
        await call.message.answer(msg)


async def schedule(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    msg = "Сконфигурируйте расписание <b>самостоятельно</b> или\n" \
          "используйте параметры <b>по умолчанию</b>\n\n" \
          "(уведомления будут приходить с понедельника по пятницу)"
    await Telegram.send_message(
        call.message.chat.id,
        msg,
        reply_markup=start_callback_keyboard(Schedule, ["Я сделаю все сам", "По умолчанию"]),
        parse_mode="HTML"
    )
    await state.set_state(ScheduleState.weekdays)


async def disable_schedule(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    if scheduler.get_job(str(call.from_user.id)):
        scheduler.remove_job(str(call.from_user.id))
    await Telegram.send_message(
        call.from_user.id, "Уведомление успешно отменено!"
    )


async def approaches(message: types.Message, state: FSMContext, subscriber: Subscriber):
    await state.clear()
    if program_id := subscriber.training_program:
        trainings = iter(Iterable([
            training.id for training in
            await get_trainings({"program_id": program_id})
        ]))
        instances = iter(
            Cycle(await get_approaches(
                message.from_user, {"training_id": next(trainings)}
            ))
        )
        if trainings.loop and instances.loop:
            approach = next(instances)
            await Telegram.send_message(
                message.from_user.id, approach.message,
                reply_markup=create_training_keyboard(), parse_mode="HTML"
            )
            await state.update_data({"trainings": trainings, "approaches": instances})
            await state.set_state(ApproachState.next_approach)
        else:
            await message.reply(
                "Текущая программа тренировок находится в разработке."
            )
    else:
        await message.reply(
            "Программа не найдена. Подпишитесь на одну из доступных программ"
        )
