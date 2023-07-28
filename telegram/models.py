import json

from dataclasses import dataclass
from typing import List

from settings import config


def cached(data_list, attr, value):
    for item in data_list:
        if item.get(attr) == value:
            return item


@dataclass
class TrainingProgramGroup:
    name: str
    description: str


@dataclass
class Training:
    pass


@dataclass
class TrainingProgram:
    name: str
    description: str
    image: str
    weeks: int
    trainings: List[Training]
    group: TrainingProgramGroup


@dataclass
class Subscriber:
    id: int
    age: int
    height: float
    weight: float
    training_program: TrainingProgram
    sport_nutrition: any
    gender: str = 'helicopter'


@dataclass(init=False)
class Token:

    def __init__(self, **kwargs):
        if data := kwargs.get("data_list", None):
            data = cached(
                kwargs.pop("data_list"),
                "telegram_id",
                kwargs.get("telegram_id")
            )
        data = kwargs if data is None else data
        for attr, value in data.items():
            setattr(self, attr, value)

    telegram_id: str
    chat_id: str = config.get("chat_id")
    access: str = ''
    refresh: str = ''

    def access_data(self):
        return {"Authorization": "Bearer {access}".format(access=self.access)}

    def post_data(self):
        return {"telegram_id": self.telegram_id, "chat_id": self.chat_id}

    def refresh_data(self):
        return {"refresh": self.refresh}


@dataclass(init=False)
class TelegramUser:
    def __init__(self, **kwargs):
        if data := kwargs.get("data_list", None):
            data = cached(
                kwargs.pop("data_list"),
                "telegram_id",
                kwargs.get("telegram_id")
            )
        data = data if data else kwargs
        for attr, value in data.items():
            setattr(self, attr, value)

    telegram_id: str
    id: int = None
    chat_id: str = config.get("chat_id")
    access: str = ''
    refresh: str = ''
    first_name: str = ''
    last_name: str = ''
    balance: float = 0
    subscriber: Subscriber = None

    def post_data(self):
        return {
            "telegram_id": self.telegram_id,
            "chat_id": self.chat_id,
            "first_name": self.first_name,
            "last_name": self.last_name
        }
