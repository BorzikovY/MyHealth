from typing import Callable, Dict, Any, Awaitable, Tuple
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from api import ApiClient, create_anonymous_user
from models import TelegramUser, Token, Subscriber


async def is_authenticated(client, data) -> Subscriber:
    user: TelegramUser = await client.get_user(*data, cache=True)

    if subscriber := user.subscriber:
        return subscriber


async def is_registered(client, data) -> Tuple[TelegramUser, Token]:
    instance: TelegramUser = create_anonymous_user(data)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        return instance, token


class RegisterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        client = ApiClient()
        if args := await is_registered(client, event.from_user):
            data.update({"client": client, "args": args})
            await handler(event, data)
        else:
            await event.answer("Введите /start, чтобы зарегистрироваться")


class SubscribeMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        client = ApiClient()
        if args := await is_registered(client, event.from_user):
            if subscriber := await is_authenticated(client, args):
                data.update({"client": client, "subscriber": subscriber})
                await handler(event, data)
            else:
                return event.answer("Нажмите на кнопку <b>Подписаться 🎁</b>", parse_mode="HTML")
        else:
            await event.answer("Введите /start, чтобы зарегистрироваться")
