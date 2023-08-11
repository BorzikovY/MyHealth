import os
import json
import asyncio
import ssl
from typing import List, Callable

import jwt

import aiofiles
from aiohttp import ClientSession
from aiogram import Bot

from models import (
    TelegramUser,
    Token,
    TrainingProgram,
    Subscriber,
    Nutrition,
    Training,
    Approach,
    Portion
)
from settings import (
    SECRET_KEY,
    HOST,
    ADMIN_TELEGRAM_ID,
    ADMIN_CHAT_ID,
    CACHE_UPDATE_TIME,
    BOT_TOKEN
)

program_lock = asyncio.Lock()
nutrition_lock = asyncio.Lock()
training_lock = asyncio.Lock()
portion_lock = asyncio.Lock()

Telegram = Bot(token=BOT_TOKEN)


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


def format_data(func: Callable):
    async def wrapper(self, data, *args, **kwargs):
        return await func(self, self.from_json(data), *args, **kwargs)
    return wrapper


def set_formatter(cls):
    attrs = [name for name in dir(cls) if name.startswith("update")]
    for attr in attrs:
        update = format_data(getattr(cls, attr))
        setattr(cls, attr, update)
    return cls


@set_formatter
class JsonCacheHandler(BaseCacheHandler):
    files = {
        "users": "users/{file}",
        "tokens": "tokens/{file}",
        "programs": "programs/{file}",
        "nutritions": "nutritions/{file}",
        "trainings": "trainings/{file}",
        "portions": "portions/{file}"
    }
    ext = "json"

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

    async def get_programs(self, data: dict, _id: str) -> List[TrainingProgram]:
        if data.get(_id):
            program = self.from_json(await self.programs.get(f"{data[_id]}.{self.ext}"))
            return TrainingProgram(**program) if program else None

        programs = [json.loads(content) for content in await self.programs.get_all()]
        instances = [TrainingProgram(**program) for program in programs]

        return [instance for instance in instances if instance.filter(data)]

    async def get_nutritions(self, data: dict, _id: str) -> List[Nutrition]:
        if data.get(_id):
            nutrition = self.from_json(await self.nutritions.get(f"{data[_id]}.{self.ext}"))
            return Nutrition(**nutrition) if nutrition else None

        nutritions = [json.loads(content) for content in await self.nutritions.get_all()]

        return [Nutrition(**nutrition) for nutrition in nutritions] if nutritions else None

    async def get_trainings(self, data: dict, _id: str) -> List[Training]:
        if data.get(_id):
            training = self.from_json(await self.trainings.get(f"{data[_id]}.{self.ext}"))
            return Training(**training) if training else None

        trainings = [json.loads(content) for content in await self.trainings.get_all()]
        instances = [Training(**training) for training in trainings]

        return [instance for instance in instances if instance.filter(data)]

    async def get_portions(self, data: dict, _id: str) -> List[Portion]:
        if data.get(_id):
            portion = self.from_json(await self.portions.get(f"{data[_id]}.{self.ext}"))
            return Portion(**portion) if portion else None

        portions = [json.loads(content) for content in await self.portions.get_all()]
        instances = [Portion(**portion) for portion in portions]

        return [instance for instance in instances if instance.filter(data)]

    async def get_user(self, data: dict, _id: str) -> TelegramUser:
        async with self.user_lock:
            user = self.from_json(await self.users.get(
                f"{data.get(_id)}.{self.ext}"
            ))

        return TelegramUser(**user) if user else None

    async def get_token(self, data: dict, _id: str) -> Token:
        async with self.token_lock:
            token = self.from_json(await self.tokens.get(
                f"{data.get(_id)}.{self.ext}"
            ))

        return Token(**token) if token else None

    async def update_programs(self, formatted_data: dict, _id: str):
        async with program_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.programs.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_nutritions(self, formatted_data: dict, _id: str):
        async with nutrition_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.nutritions.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_trainings(self, formatted_data: dict, _id: str):
        async with training_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.trainings.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_portions(self, formatted_data: dict, _id: str):
        async with portion_lock:
            tasks = []
            for data in formatted_data:
                tasks.append(self.portions.post(json.dumps(data), f"{data.get(_id)}.{self.ext}"))
            await asyncio.gather(*tasks)

    async def update_token(self, formatted_data: dict, _id: str) -> None:
        payload = jwt.decode(
            formatted_data.get("access"),
            SECRET_KEY, algorithms=["HS256"]
        )
        async with self.token_lock:
            await self.tokens.post(self.to_json(formatted_data), f"{payload.get(_id)}.{self.ext}")

    async def update_subscriber(self, formatted_data: dict, _id: str):
        existing_data = self.from_json(await self.users.get(
            f"{formatted_data.get(_id)}.{self.ext}"
        ))
        existing_data.update({"subscriber": formatted_data})
        async with self.user_lock:
            await self.users.post(
                self.to_json(existing_data),
                f"{formatted_data.get(_id)}.{self.ext}"
            )

    async def update_user(self, formatted_data: dict, _id: str) -> None:
        existing_data = self.from_json(await self.users.get(
            f"{formatted_data.get(_id)}.{self.ext}"
        ))
        existing_data.update(formatted_data)
        async with self.user_lock:
            await self.users.post(
                self.to_json(formatted_data),
                f"{formatted_data.get(_id)}.{self.ext}"
            )


async def auth_user(client, registered_user: TelegramUser) -> TelegramUser:
    asyncio.create_task(client.get_token(registered_user))
    return registered_user


async def register_user(client, anonymous_user: TelegramUser) -> TelegramUser:
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


async def get_programs(data: dict = None) -> List[TrainingProgram] | List:
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: list[TrainingProgram] = await client.get_programs(
            instance, token,
            cache=True, data=data
        )
        return instances
    return []


async def get_program(message, data: dict = None) -> TrainingProgram | None:
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(data=message)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        program: TrainingProgram = await client.get_program(
            instance, token,
            cache=True,
            data=data
        )
        return program
    return None


async def get_approaches(message, data) -> List[Approach]:
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: list[TrainingProgram] = await client.get_approaches(
            instance, token,
            cache=True, data=data
        )
        return instances
    return []


async def get_nutritions(data: dict = None) -> List[Nutrition] | List:
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: List[Nutrition] = await client.get_nutritions(
            instance, token,
            cache=True, data=data
        )
        return instances
    return []


async def get_nutrition(message, data: dict = None) -> Nutrition | None:
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(data=message)

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        nutrition: Nutrition = await client.get_nutrition(
            instance, token,
            cache=True,
            data=data
        )
        return nutrition
    return None


async def get_trainings(data: dict = None) -> List[Training] | List:
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: List[Training] = await client.get_trainings(
            instance, token,
            cache=True, data=data
        )
        return instances
    return []


async def get_portions(data: dict = None) -> List[Portion] | List:
    client = ApiClient()
    instance: TelegramUser = create_admin_user()

    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        instances: List[Portion] = await client.get_portions(
            instance, token,
            cache=True, data=data
        )
        return instances
    return []


async def update_subscribe(message, data: dict) -> bool | None:
    client = ApiClient()
    instance: TelegramUser = create_anonymous_user(message)
    token: Token = await client.get_token(instance)
    if isinstance(token, Token):
        user = await client.update_user(
            instance, token,
            data={"subscriber": data}
        )
        return isinstance(user, TelegramUser)
    return None


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

    @staticmethod
    def set_query_data(url: str, data: dict):
        if data:
            params = "&".join(
                [f"{key}={value}" for key, value in data.items()]
            )
            url += f"?{params}"
        return url

    async def send_request(
            self,
            url, headers, method, status,
            model, _id_field, cache_function=None,
            **data
    ):
        sslcontext = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        async with ClientSession(headers=headers) as session:
            request = getattr(session, method)
            response = await request(url, ssl=sslcontext, **data)

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
    async def get_cache(_id_field, data, cache_function):
        data = data if data is not None else {}
        instance = await cache_function(data, _id_field)
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
            await asyncio.sleep(CACHE_UPDATE_TIME)

    async def update_nutrition_cache(self, admin: TelegramUser):
        while True:
            token: Token = await self.get_token(admin)
            if isinstance(token, Token):
                await self.get_nutritions(admin, token, data=None, cache=False)
            await asyncio.sleep(CACHE_UPDATE_TIME)

    async def update_training_cache(self, admin: TelegramUser):
        while True:
            token: Token = await self.get_token(admin)
            if isinstance(token, Token):
                await self.get_trainings(admin, token, data=None, cache=False)
            await asyncio.sleep(CACHE_UPDATE_TIME)

    async def update_portion_cache(self, admin: TelegramUser):
        while True:
            token: Token = await self.get_token(admin)
            if isinstance(token, Token):
                await self.get_portions(admin, token, data=None, cache=False)
            await asyncio.sleep(CACHE_UPDATE_TIME)

    async def update_cache(self, dispatcher):
        instance: TelegramUser = create_admin_user()
        asyncio.create_task(self.update_program_cache(instance))
        asyncio.create_task(self.update_nutrition_cache(instance))
        asyncio.create_task(self.update_training_cache(instance))
        asyncio.create_task(self.update_portion_cache(instance))

    async def get_token(self, user: TelegramUser, cache=True):
        url = f"{self.base_url}/api/token/"
        if cache:
            token = await self.get_cache(
                "telegram_id", user.access_data(), self.handler.get_token
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
    async def get_user(self, user: TelegramUser, token: Token, **kwargs) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        if kwargs.get("cache"):
            user = await self.get_cache(
                "telegram_id", token.post_data(), self.handler.get_user
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
    async def get_programs(self, user: TelegramUser, token: Token, **kwargs) -> List[TrainingProgram]:
        url = f"{self.base_url}/api/program/list/"
        if kwargs.get("cache") and not program_lock.locked():
            programs = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_programs
            )
            if programs is not None:
                return programs
        url = self.set_query_data(url, kwargs.get("data"))
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
    async def get_program(self, user: TelegramUser, token: Token, **kwargs) -> TrainingProgram:
        if kwargs.get("cache") and not program_lock.locked():
            program = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_programs
            )
            if program is not None:
                return program
        url = f"{self.base_url}/api/program/{kwargs.get('data', {}).get('id', 0)}/"
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
    async def get_nutritions(self, user: TelegramUser, token: Token, **kwargs) -> List[Nutrition]:
        url = f"{self.base_url}/api/nutrition/list/"
        if kwargs.get("cache") and not nutrition_lock.locked():
            nutritions = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_nutritions
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
            self.handler.update_nutritions if not kwargs.get("cache") else None
        )

    @check_token
    async def get_nutrition(self, user: TelegramUser, token: Token, **kwargs) -> Nutrition:
        if kwargs.get("cache") and not nutrition_lock.locked():
            nutrition = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_nutritions
            )
            if nutrition is not None:
                return nutrition
        url = f"{self.base_url}/api/nutrition/{kwargs.get('data', {}).get('id', 0)}/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Nutrition,
            "id"
        )

    @check_token
    async def get_trainings(self, user: TelegramUser, token: Token, **kwargs) -> List[Training]:
        url = f"{self.base_url}/api/training/list/"
        if kwargs.get("cache") and not training_lock.locked():
            trainings = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_trainings
            )
            if trainings is not None:
                return trainings
        url = self.set_query_data(url, kwargs.get("data"))
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
    async def get_portions(self, user: TelegramUser, token: Token, **kwargs) -> List[Portion]:
        url = f"{self.base_url}/api/portion/list/"
        if kwargs.get("cache") and not portion_lock.locked():
            portions = await self.get_cache(
                "id", kwargs.get("data"), self.handler.get_portions
            )
            if portions is not None:
                return portions
        url = self.set_query_data(url, kwargs.get("data"))
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Portion,
            "id",
            self.handler.update_portions if not kwargs.get("cache") else None
        )

    @check_token
    async def get_approaches(self, user: TelegramUser, token: Token, **kwargs) -> List[Approach]:
        url = f"{self.base_url}/api/approach/list/"
        if kwargs.get("data"):
            params = "&".join(
                [f"{key}={value}" for key, value in kwargs["data"].items()]
            )
            url += f"?{params}"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "get",
            200,
            Approach,
            "id"
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
            "telegram_id",
            self.handler.update_subscriber,
            data=json.dumps(token.post_data())
        )

    @check_token
    async def update_user(self, user: TelegramUser, token: Token, **kwargs) -> TelegramUser:
        url = f"{self.base_url}/api/user/"
        headers = self.get_headers(token.access_data())
        return await self.send_request(
            url,
            headers,
            "put",
            200,
            TelegramUser,
            "telegram_id",
            self.handler.update_user,
            data=json.dumps(kwargs.get("data", {}))
        )
