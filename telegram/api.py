import os
import json
import asyncio

import aiofiles
from aiohttp import ClientSession

from models import TelegramUser, Token

user_lock = asyncio.Lock()
token_lock = asyncio.Lock()


class IOHandler:

    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def to_bytes(value):
        return value.encode("utf-8")

    async def post(self, data: bytes | str):
        data = data if isinstance(data, bytes) else self.to_bytes(data)
        async with aiofiles.open(self.path, "wb+") as file:
            await file.write(data)

    async def get(self):
        if os.path.exists(self.path):
            async with aiofiles.open(self.path, "rb+") as file:
                data = await file.read()
                return data.decode()
        return "[]"


class BaseCacheHandler:

    files = {}
    cache_dir = os.path.join(os.path.abspath(""), "cache")

    def __init__(self):
        for attr, file in self.files.items():
            path = os.path.join(self.cache_dir, file)
            setattr(self, attr, IOHandler(path))


class JsonCacheHandler(BaseCacheHandler):
    files = {
        "users": "users.json",
        "tokens": "tokens.json"
    }

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
        async with user_lock:
            users = json.loads(await self.users.get())
        data["data_list"] = users
        user = TelegramUser(**data)
        return user

    async def get_token(self, data: dict) -> Token:
        async with token_lock:
            tokens = json.loads(await self.tokens.get())
        data["data_list"] = tokens
        token = Token(**data)
        return token

    async def update_tokens(self, new: str) -> None:
        received = self.from_json(new)
        data = self.from_json(await self.tokens.get())
        formatted_data = self.to_json(data + [received])
        async with token_lock:
            await self.tokens.post(formatted_data)

    async def update_users(self, new: str) -> None:
        received = self.from_json(new)
        data = self.from_json(await self.users.get())
        formatted_data = self.to_json(data + [received])
        async with user_lock:
            await self.users.post(formatted_data)


class ApiClient:

    cache_class = JsonCacheHandler

    def __init__(self, base_url):
        self.handler = self.cache_class()
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }

    async def clear_cache(self, dispatcher):
        for value in self.handler.files:
            if os.path.exists(getattr(self.handler, value).path):
                os.remove(getattr(self.handler, value).path)

    def get_refreshed_token(self, data):
        pass

    async def get_new_token(self, user: TelegramUser):
        url = f"{self.base_url}/api/token/"
        async with ClientSession(headers=self.headers) as session:
            response = await session.post(url, data=json.dumps(user.post_data()))
            content = (await response.read()).decode()
            if response.status == 200:
                asyncio.create_task(
                    self.handler.update_tokens(content)
                )
                return Token(**self.handler.from_json(content))
        return self.handler.from_json(content)

    async def create_user(self, user: TelegramUser) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        async with ClientSession(headers=self.headers) as session:
            response = await session.post(url, data=json.dumps(user.post_data()))
            content = (await response.read()).decode()
            if response.status == 201:
                asyncio.create_task(
                    self.handler.update_users(content)
                )
                return TelegramUser(**self.handler.from_json(content))
        return self.handler.from_json(content)

    async def get_user(self, token: Token) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        tg_user = await self.handler.get_user(token.post_data())
        if tg_user.id is not None:
            return tg_user
        self.headers.update(token.access_data())
        async with ClientSession(headers=self.headers) as session:
            response = await session.get(url)
            content = (await response.read()).decode()
            if response.status == 200:
                asyncio.create_task(
                    self.handler.update_users(content)
                )
                return TelegramUser(**self.handler.from_json(content))
        return self.handler.from_json(content)
