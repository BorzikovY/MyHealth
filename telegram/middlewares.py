from typing import Callable, Dict, Any, Awaitable, Tuple
from aiogram import BaseMiddleware
from aiogram.types import Message

from api import ApiClient, create_anonymous_user
from models import TelegramUser, Token


async def is_authenticated(client, data):
    pass


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
        state = data.get("state")
        await state.clear()
        client = ApiClient()

        if args := await is_registered(client, event.from_user):
            data["client"] = client
            data["args"] = args
            await handler(event, data)
        else:
            return event.answer("Введите /start, чтобы зарегистрироваться")


class SubscribeMiddleware(RegisterMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        state = data.get("state")
        await state.clear()
        client = ApiClient()

        if args := await is_registered(client, event.from_user):
            data["client"] = client
            data["args"] = args
            await handler(event, data)
        else:
            return event.answer("Введите /start, чтобы зарегистрироваться")

