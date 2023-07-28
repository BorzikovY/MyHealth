import os
import json
import asyncio

import jwt

import aiofiles
from aiohttp import ClientSession

from models import TelegramUser, Token
from settings import config, SECRET_KEY


class IOHandler:

    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def to_bytes(value):
        return value.encode("utf-8")

    async def post(self, data: bytes | str, name: str):
        path = self.path.format(file=f"{name}.json")
        directory = self.path.format(file="")
        if not os.path.exists(directory):
            os.mkdir(directory)
        data = data if isinstance(data, bytes) else self.to_bytes(data)
        async with aiofiles.open(path, "wb+") as file:
            await file.write(data)

    async def get(self, name: str):
        path = self.path.format(file=f"{name}.json")
        if os.path.exists(path):
            async with aiofiles.open(path, "rb+") as file:
                data = await file.read()
                return data.decode()
        return "{}"


class BaseCacheHandler:

    files = {}
    cache_dir = os.path.join(os.path.abspath(""), "cache")

    def __init__(self):
        for attr, file in self.files.items():
            path = os.path.join(self.cache_dir, file)
            setattr(self, attr, IOHandler(path))


class JsonCacheHandler(BaseCacheHandler):
    files = {
        "users": "users/{file}",
        "tokens": "tokens/{file}"
    }

    def __init__(self):
        super().__init__()
        self.user_lock = asyncio.Lock()
        self.token_lock = asyncio.Lock()

    @staticmethod
    def to_json(data) -> str:
        if data:
            return json.dumps(data)
        return "{}"

    @staticmethod
    def from_json(data) -> dict:
        if data:
            return json.loads(data)
        return {}

    async def get_user(self, data: dict) -> TelegramUser:
        async with self.user_lock:
            user = json.loads(await self.users.get(
                data.get("telegram_id")
            ))
        if user:
            return TelegramUser(**user)

    async def get_token(self, data: dict) -> Token:
        async with self.token_lock:
            token = json.loads(await self.tokens.get(
                data.get("telegram_id")
            ))
        if token:
            return Token(**token)

    async def update_tokens(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        payload = jwt.decode(
            formatted_data.get("access"),
            SECRET_KEY, algorithms=["HS256"]
        )
        async with self.token_lock:
            await self.tokens.post(received, payload.get(_id))

    async def update_users(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        async with self.user_lock:
            await self.users.post(received, formatted_data.get(_id))


class ApiClient:

    cache_class = JsonCacheHandler

    def __init__(self, base_url):
        self.handler = self.cache_class()
        self.base_url = base_url

    @staticmethod
    def get_headers(data: dict = None):
        headers = {
            "Content-Type": "application/json"
        }
        if data is not None:
            headers.update(data)
        return headers

    async def send_request(
            self,
            url, headers, method, status,
            model, _id_field, cache_function,
            **data
    ):
        async with ClientSession(headers=headers) as session:
            request = getattr(session, method)
            response = await request(url, **data)
            content = (await response.read()).decode()
            if response.status == status:
                asyncio.create_task(
                    cache_function(content, _id_field)
                )
                return model(**self.handler.from_json(content))
        return self.handler.from_json(content)

    @staticmethod
    async def get_cache(data, cache_function):
        instance = await cache_function(data)
        return instance

    @staticmethod
    def check_token(coro):
        async def wrapper(self, user, token, cache=True):
            try:
                if not token.payload:
                    raise jwt.exceptions.ExpiredSignatureError("Token is expired")
                return await coro(self, user, token, cache)
            except jwt.exceptions.ExpiredSignatureError:
                token = await self.get_token(
                    TelegramUser(**user.post_data()), False
                )
            finally:
                if isinstance(token, Token):
                    return await coro(self, user, token, cache)
                return token
        return wrapper

    async def clear_cache(self, dispatcher):
        for value in self.handler.files:
            path = getattr(self.handler, value).path.format(file="")
            if os.path.exists(path):
                for file in os.listdir(path):
                    if os.path.exists(os.path.join(path, file)):
                        os.remove(os.path.join(path, file))

    async def get_token(self, user: TelegramUser, cache=True):
        url = f"{self.base_url}/api/token/"
        if cache:
            token = await self.get_cache(
                user.access_data(), self.handler.get_token
            )
            if token is not None:
                return token
        headers = self.get_headers()
        return await self.send_request(
            url,
            headers,
            "post",
            200,
            Token,
            "telegram_id",
            self.handler.update_tokens,
            data=json.dumps(user.access_data())
        )

    async def create_user(self, user: TelegramUser) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        headers = self.get_headers()
        return await self.send_request(
            url,
            headers,
            "post",
            201,
            TelegramUser,
            "telegram_id",
            self.handler.update_users,
            data=json.dumps(user.post_data())
        )

    @check_token
    async def get_user(self, user: TelegramUser, token: Token, cache=True) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        if cache:
            user = await self.get_cache(
                token.post_data(), self.handler.get_user
            )
            if user is not None:
                return user
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            TelegramUser,
            "telegram_id",
            self.handler.update_users
        )
