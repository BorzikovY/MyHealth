import os
import json
import asyncio
from typing import List

import jwt

import aiofiles
from aiohttp import ClientSession

from models import TelegramUser, Token, TrainingProgram, Subscriber, Nutrition, Training
from settings import SECRET_KEY, HOST

program_lock = asyncio.Lock()
nutrition_lock = asyncio.Lock()
training_lock = asyncio.Lock()


class IOHandler:

    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def to_bytes(value):
        return value.encode("utf-8")

    async def post(self, data: bytes | str, name: str):
        path = self.path.format(file=f"{name}")
        directory = self.path.format(file="")
        if not os.path.exists(directory):
            os.mkdir(directory)
        data = data if isinstance(data, bytes) else self.to_bytes(data)
        async with aiofiles.open(path, "wb+") as file:
            await file.write(data)

    async def get(self, name: str):
        path = self.path.format(file=f"{name}")
        if os.path.exists(path):
            async with aiofiles.open(path, "rb+") as file:
                data = await file.read()
                return data.decode()
        return "{}"

    async def get_all(self):
        tasks = []
        if not os.path.exists(self.path.format(file="")):
            return []
        for name in os.listdir(self.path.format(file="")):
            tasks.append(self.get(name))
        return await asyncio.gather(*tasks)


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
        "tokens": "tokens/{file}",
        "subscribers": "subscribers/{file}",
        "programs": "programs/{file}",
        "nutritions": "nutritions/{file}",
        "trainings": "trainings/{file}"
    }
    ext = "json"

    def __init__(self):
        super().__init__()
        self.user_lock = asyncio.Lock()
        self.token_lock = asyncio.Lock()
        self.subscriber_lock = asyncio.Lock()

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

    async def get_programs(self, data: dict) -> List[TrainingProgram]:
        async with program_lock:
            programs = [json.loads(content) for content in await self.programs.get_all()]
        if programs:
            instances = [TrainingProgram(**program).filter(**data) for program in programs]
            return [instance for instance in instances if instance is not None]
        
    async def get_nutritions(self, data: dict) -> List[Nutrition]:
        async with nutrition_lock:
            nutritions = [json.loads(content) for content in await self.nutritions.get_all()]
        if nutritions:
            return [Nutrition(**nutrition) for nutrition in nutritions]
        
    async def get_trainings(self, data: dict) -> List[Training]:
        async with training_lock:
            trainings = [json.loads(content) for content in await self.trainings.get_all()]
        if trainings:
            return [Training(**training) for training in trainings]

    async def get_user(self, data: dict) -> TelegramUser:
        async with self.user_lock:
            user = json.loads(await self.users.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))
        if user:
            return TelegramUser(**user)

    async def get_token(self, data: dict) -> Token:
        async with self.token_lock:
            token = json.loads(await self.tokens.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))
        if token:
            return Token(**token)

    async def get_subscriber(self, data: dict) -> Subscriber:
        async with self.subscriber_lock:
            subscriber = json.loads(await self.subscribers.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))
        if subscriber:
            return Subscriber(**subscriber)

    async def update_programs(self, received: str, _id: str):
        formatted_data = json.loads(received)
        async with program_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.programs.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_nutritions(self, received: str, _id: str):
        formatted_data = json.loads(received)
        async with nutrition_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.nutritions.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_trainings(self, received: str, _id: str):
        formatted_data = json.loads(received)
        async with training_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.trainings.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_token(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        payload = jwt.decode(
            formatted_data.get("access"),
            SECRET_KEY, algorithms=["HS256"]
        )
        async with self.token_lock:
            await self.tokens.post(received, f"{payload.get(_id)}.{self.ext}")

    async def update_user(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        async with self.user_lock:
            await self.users.post(received, f"{formatted_data.get(_id)}.{self.ext}")

    async def update_subscriber(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        async with self.subscriber_lock:
            await self.subscribers.post(received, f"{formatted_data.get(_id)}.{self.ext}")

    async def update_program(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        async with program_lock:
            await self.programs.post(received, f"{formatted_data.get(_id)}.{self.ext}")

    async def update_nutrition(self, received: str, _id: str) -> None:
        formatted_data = json.loads(received)
        async with nutrition_lock:
            await self.nutritions.post(received, f"{formatted_data.get(_id)}.{self.ext}")


class ApiClient:

    cache_class = JsonCacheHandler

    def __init__(self):
        self.handler = self.cache_class()
        self.base_url = HOST

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
                output = self.handler.from_json(content)
                if isinstance(output, list):
                    return [model(**data) for data in output]
                return model(**output)
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
            self.handler.update_token,
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
            self.handler.update_user,
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
            self.handler.update_user
        )

    @check_token
    async def get_programs(
            self,
            user: TelegramUser,
            token: Token,
            data: dict | None,
            cache=True) -> List[TrainingProgram]:
        url = f"{self.base_url}/api/program/list/"
        if cache and not program_lock.locked():
            programs = await self.get_cache(
                data, self.handler.get_programs
            )
            if programs is not None:
                return programs
        if data:
            params = "&".join([f"{key}={value}" for key, value in data.items()])
            url += f"?{params}"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            TrainingProgram,
            "id",
            self.handler.update_programs
        )

    @check_token
    async def get_nutritions(self, user: TelegramUser, token: Token, cache=True) -> Nutrition:
        url = f"{self.base_url}/api/nutrition/list/"
        if cache and not nutrition_lock.locked():
            nutritions = await self.get_cache(
                {}, self.handler.get_nutritions
            )
            if nutritions is not None:
                return nutritions
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Nutrition,
            "id",
            self.handler.update_nutritions
        )

    @check_token
    async def get_trainings(self, user: TelegramUser, token: Token, cache=True) -> Training:
        url = f"{self.base_url}/api/training/list/?program_id=2"
        if cache and not training_lock.locked():
            trainings = await self.get_cache(
                {}, self.handler.get_trainings
            )
            if trainings is not None:
                return trainings
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Training,
            "id",
            self.handler.update_trainings
        )

    @check_token
    async def create_subscriber(self, user: TelegramUser, token: Token, cache=True) -> Subscriber:
        url = f"{self.base_url}/api/subscribe/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "post",
            201,
            Subscriber,
            "id",
            self.handler.update_subscriber,
            data=json.dumps(token.post_data())
        )

    @check_token
    async def get_program(self, user: TelegramUser, token: Token, cache=True) -> TrainingProgram:
        url = f"{self.base_url}/api/program/1/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            TrainingProgram,
            "id",
            self.handler.update_program
        )

    @check_token
    async def get_nutrition(self, user: TelegramUser, token: Token, cache=True) -> Nutrition:
        url = f"{self.base_url}/api/nutrition/1/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Nutrition,
            "id",
            self.handler.update_nutrition
        )