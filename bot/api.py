import os
import json
import asyncio
from typing import Coroutine

import aiofiles

from aiohttp import ClientSession


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
        async with aiofiles.open(self.path, "wb") as file:
            await file.write(data)

    async def get(self):
        async with aiofiles.open(self.path, "rb") as file:
            data = await file.read()
            return data.decode()


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
        return []

    @staticmethod
    def from_json(data) -> list:
        if data:
            return json.loads(data)
        return []

    async def get_users(self):
        async with user_lock:
            return await self.users.get()

    async def get_tokens(self):
        async with token_lock:
            return await self.tokens.get()

    async def update_users(self, new):
        received = self.from_json(new)
        data = self.from_json(await self.get_users())
        formatted_data = self.to_json(data + [received])
        async with user_lock:
            await self.users.post(formatted_data)

    async def update_tokens(self, new):
        received = self.from_json(new)
        data = self.from_json(self.get_tokens())
        formatted_data = self.to_json(data + [received])
        async with token_lock:
            await self.tokens.post(formatted_data)


class ApiClient:

    cache_class = JsonCacheHandler

    def __init__(self, base_url):
        self.handler = self.cache_class()
        self.base_url = base_url

    def get_refreshed_token(self, data):
        pass

    async def get_new_token(self, data):
        url = f"{self.base_url}/token"
        async with ClientSession() as session:
            response = await session.post(url, data=data)
            content = (await response.read()).decode()
            if response.status == 200:
                asyncio.create_task(
                    self.handler.update_tokens(content)
                )
        return self.handler.from_json(content)

    async def create_user(self, data):
        url = f"{self.base_url}/user"
        async with ClientSession() as session:
            response = await session.post(url, data=data)
            content = (await response.read()).decode()
            if response.status == 200:
                asyncio.create_task(
                    self.handler.update_users(content)
                )
        return self.handler.from_json(content)

    def authenticate_user(self, data):
        url = f""
