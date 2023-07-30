import os
import json
import asyncio
from typing import List

import jwt

import aiofiles
from aiohttp import ClientSession

from models import TelegramUser, Token, TrainingProgram, Subscriber, Nutrition, Training
from settings import SECRET_KEY, HOST, ADMIN_TELEGRAM_ID, ADMIN_CHAT_ID

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
        if data.get("id"):
            program = json.loads(await self.programs.get(f"{data['id']}.{self.ext}"))
            return TrainingProgram(**program) if program else None

        programs = [json.loads(content) for content in await self.programs.get_all()]
        instances = [TrainingProgram(**program) for program in programs]

        return [instance for instance in instances if instance.filter(data)]

    async def get_nutritions(self, data: dict) -> List[Nutrition]:
        if data.get("id"):
            nutrition = json.loads(await self.nutritions.get(f"{data['id']}.{self.ext}"))
            return Nutrition(**nutrition) if nutrition else None

        nutritions = [json.loads(content) for content in await self.nutritions.get_all()]

        return [Nutrition(**nutrition) for nutrition in nutritions] if nutritions else None

    async def get_trainings(self, data: dict) -> List[Training]:
        trainings = [json.loads(content) for content in await self.trainings.get_all()]

        return [Training(**training) for training in trainings] if trainings else None

    async def get_user(self, data: dict) -> TelegramUser:
        async with self.user_lock:
            user = json.loads(await self.users.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))

        return TelegramUser(**user) if user else None

    async def get_token(self, data: dict) -> Token:
        async with self.token_lock:
            token = json.loads(await self.tokens.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))

        return Token(**token) if token else None

    async def get_subscriber(self, data: dict) -> Subscriber:
        async with self.subscriber_lock:
            subscriber = json.loads(await self.subscribers.get(
                f"{data.get('telegram_id')}.{self.ext}"
            ))

        return Subscriber(**subscriber) if subscriber else None

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


async def auth_user(client, registered_user: TelegramUser):
    asyncio.create_task(client.get_token(registered_user))
    return registered_user


async def register_user(client, anonymous_user: TelegramUser):
    telegram_user = await client.create_user(anonymous_user)
    if isinstance(telegram_user, TelegramUser):
        return await auth_user(client, telegram_user)


def create_anonymous_user(data) -> TelegramUser:
    return TelegramUser(
        telegram_id=str(data.id),
        first_name=data.first_name,
        last_name=data.last_name
    )


def create_admin_user() -> TelegramUser:
    return TelegramUser(
        telegram_id=ADMIN_TELEGRAM_ID,
        chat_id=ADMIN_CHAT_ID
    )


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
            model, _id_field, cache_function=None,
            **data
    ):
        async with ClientSession(headers=headers) as session:
            request = getattr(session, method)
            response = await request(url, **data)
            content = (await response.read()).decode()
            if response.status == status:
                if cache_function is not None:
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
        data = data if data is not None else {}
        instance = await cache_function(data)
        return instance

    @staticmethod
    def check_token(coro):
        async def wrapper(self, user, token, **kwargs):
            try:
                if not token.payload:
                    raise jwt.exceptions.ExpiredSignatureError("Token is expired")
                return await coro(self, user, token, **kwargs)
            except jwt.exceptions.ExpiredSignatureError:
                token = await self.get_token(
                    TelegramUser(**user.post_data()), False
                )
            finally:
                if isinstance(token, Token):
                    return await coro(self, user, token, **kwargs)
                return token
        return wrapper

    async def clear_cache(self, dispatcher):
        for value in self.handler.files:
            path = getattr(self.handler, value).path.format(file="")
            if os.path.exists(path):
                for file in os.listdir(path):
                    if os.path.exists(os.path.join(path, file)):
                        os.remove(os.path.join(path, file))

    async def update_program_cache(self, admin: TelegramUser):
        while True:
            token: Token = await self.get_token(admin)
            if isinstance(token, Token):
                await self.get_programs(admin, token, data=None, cache=False)
            await asyncio.sleep(10)

    async def update_nutrition_cache(self, admin: TelegramUser):
        while True:
            token: Token = await self.get_token(admin)
            if isinstance(token, Token):
                await self.get_nutritions(admin, token, data=None, cache=False)
            await asyncio.sleep(10)

    async def update_cache(self, dispatcher):
        instance: TelegramUser = create_admin_user()
        asyncio.create_task(self.update_program_cache(instance))
        asyncio.create_task(self.update_nutrition_cache(instance))

    async def get_token(self, user: TelegramUser, cache=True):
        url = f"{self.base_url}/api/token/"
        if cache:
            token = await self.get_cache(
                user.access_data(), self.handler.get_token
            )
            if token:
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
    async def get_user(self, user: TelegramUser, token: Token, **kwargs) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        if kwargs.get("cache"):
            user = await self.get_cache(
                token.post_data(), self.handler.get_user
            )
            if user:
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
    async def get_programs(self, user: TelegramUser, token: Token, **kwargs) -> List[TrainingProgram]:
        url = f"{self.base_url}/api/program/list/"
        if kwargs.get("cache") and not program_lock.locked():
            programs = await self.get_cache(
                kwargs.get("data"), self.handler.get_programs
            )
            if programs:
                return programs
        if kwargs.get("data"):
            params = "&".join([f"{key}={value}" for key, value in kwargs["data"].items()])
            url += f"?{params}"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            TrainingProgram,
            "id",
            self.handler.update_programs if not kwargs.get("cache") else None
        )

    @check_token
    async def get_nutritions(self, user: TelegramUser, token: Token, **kwargs) -> Nutrition:
        url = f"{self.base_url}/api/nutrition/list/"
        if kwargs.get("cache") and not nutrition_lock.locked():
            nutritions = await self.get_cache(
                kwargs.get("data"), self.handler.get_nutritions
            )
            if nutritions:
                return nutritions
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Nutrition,
            "id",
            self.handler.update_nutritions if not kwargs.get("cache") else None
        )

    @check_token
    async def get_trainings(self, user: TelegramUser, token: Token, **kwargs) -> Training:
        url = f"{self.base_url}/api/training/list/?program_id=2"
        if kwargs.get("cache") and not training_lock.locked():
            trainings = await self.get_cache(
                kwargs.get("data"), self.handler.get_trainings
            )
            if trainings:
                return trainings
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Training,
            "id",
            self.handler.update_trainings if not kwargs.get("cache") else None
        )

    @check_token
    async def create_subscriber(self, user: TelegramUser, token: Token, **kwargs) -> Subscriber:
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
    async def update_subscriber(self, user: TelegramUser, token: Token, **kwargs) -> Subscriber:
        url = f"{self.base_url}/api/subscribe/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "put",
            205,
            Subscriber,
            "id",
            self.handler.update_subscriber,
            data=json.dumps(kwargs.get("data", {}))
        )

    @check_token
    async def get_subscriber(self, user: TelegramUser, token: Token, **kwargs) -> Subscriber:
        if kwargs.get("cache"):
            subscriber = await self.get_cache(
                kwargs.get("data"), self.handler.get_subscriber
            )
            if subscriber:
                return subscriber
        url = f"{self.base_url}/api/subscribe/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Subscriber,
            "id",
            self.handler.update_subscriber,
            data=json.dumps(token.post_data())
        )

    @check_token
    async def get_program(self, user: TelegramUser, token: Token, **kwargs) -> TrainingProgram:
        if kwargs.get("cache") and not program_lock.locked():
            program = await self.get_cache(
                kwargs.get("data"), self.handler.get_programs
            )
            if program:
                return program
        data = kwargs.get("data", {})
        url = f"{self.base_url}/api/program/{data.get('id', 0)}/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            TrainingProgram,
            "id"
        )

    @check_token
    async def get_nutrition(self, user: TelegramUser, token: Token, **kwargs) -> Nutrition:
        if kwargs.get("cache") and not nutrition_lock.locked():
            nutrition = await self.get_cache(
                kwargs.get("data"), self.handler.get_nutritions
            )
            if nutrition:
                return nutrition
        data = kwargs.get("data", {})
        url = f"{self.base_url}/api/nutrition/{data.get('id')}/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Nutrition,
            "id"
        )