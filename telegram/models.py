from datetime import timedelta

import jwt
import re

from dataclasses import dataclass
from typing import List, Callable

from messages import program_message, user_message
from settings import config, SECRET_KEY


class duration(timedelta):
    def __new__(cls, string, **kwargs):
        data = enumerate(reversed((string.split(":"))))
        validated_data = map(lambda val: int(val[1]) * 60**val[0], data)
        return super(duration, cls).__new__(cls, seconds=sum(validated_data))


class DataFilter:

    EXP_FORMAT = r"(?:[<>]=?|=)"
    FILTER_EXP = {
        "<": "__gt__",
        "<=": "__ge__",
        ">": "__lt__",
        ">=": "__le__",
        "=": "__eq__"
    }
    PATTERNS = {
        float: r'([0-9]*[.])?[0-9]+',
        int: r'[-]?[0-9]+',
        duration: r'[0-9]+:[0-5][0-9]',
        str: r'.*'
    }

    @classmethod
    def filter(
            cls, string: str | None, data_class
    ) -> Callable:
        if string is not None:
            value_match, op_match = (
                re.search(cls.PATTERNS[data_class], string),
                re.search(cls.EXP_FORMAT, string)
            )
            if value_match and op_match:
                op, value = (
                    cls.FILTER_EXP[op_match.group(0)],
                    data_class(value_match.group(0))
                )
                return getattr(value, op)
        return lambda val: True


@dataclass
class Portion:
    id: int
    name: str
    description: str
    calories: int
    proteins: float
    fats: float
    carbs: float


@dataclass
class Nutrition:
    id: int
    name: str
    description: str
    dosages: str
    use: str
    contraindications: str
    portions: List[Portion]


@dataclass
class Exercise:
    id: int
    name: str
    description: str
    image: str
    video: str


@dataclass
class TrainingProgramGroup:
    name: str
    description: str


@dataclass
class Training:
    id: str
    name: str
    description: str
    difficulty: int
    time: str
    appoarch_count: str


@dataclass
class TrainingProgram:

    def __post_init__(self):
        difficulty_icon = "💪️" if self.difficulty <= 3 else "🦾️"
        group_name = self.group.name if self.group else "Общая подготовка"
        avg_training_time = self.avg_training_time if self.avg_training_time else "-"
        self.message = program_message.format(
            name=self.name, group_name=group_name,
            image="https://img2.goodfon.ru/original/1024x1024/c/e9/gym-man-woman-workout-fitness.jpg",
            difficulty=self.difficulty,
            difficulty_icon=difficulty_icon,
            weeks=self.weeks,
            training_count=self.training_count,
            avg_training_time=avg_training_time,
            description=self.description
        )

    def filter(self, data: dict | None):
        if data is not None:
            first_filter = DataFilter.filter(data.get("difficulty"), data_class=float)
            second_filter = DataFilter.filter(data.get("weeks"), data_class=int)
            return first_filter(self.difficulty) and second_filter(self.weeks)
        return True

    id: int
    name: str
    description: str
    image: str
    weeks: int
    group: TrainingProgramGroup
    avg_training_time: timedelta
    training_count: int
    difficulty: float


@dataclass
class Subscriber:
    id: int
    age: int
    height: float
    weight: float
    training_program: TrainingProgram
    gender: str = 'helicopter'
    is_adult: bool = False


@dataclass
class Token:

    access: str
    refresh: str

    def __post_init__(self):
        try:
            data = jwt.decode(self.access, SECRET_KEY, algorithms=["HS256"])
            self.payload = {
                "telegram_id": data.get("telegram_id"),
                "chat_id": config.get("chat_id")
            }
        except jwt.exceptions.ExpiredSignatureError:
            self.payload = None

    def access_data(self):
        return {"Authorization": "Bearer {access}".format(access=self.access)}

    def post_data(self):
        return self.payload

    def refresh_data(self):
        return {"refresh": self.refresh}


@dataclass
class TelegramUser:

    def __post_init__(self):
        self.message = user_message.format(
            first_name=self.first_name,
            last_name=self.last_name,
            balance=self.balance
        )

    telegram_id: str
    id: int = None
    chat_id: str = config.get("chat_id")
    access: str = ''
    refresh: str = ''
    first_name: str = ''
    last_name: str = ''
    balance: float = 0
    subscriber: int = None

    def access_data(self):
        return {
            "telegram_id": self.telegram_id,
            "chat_id": self.chat_id
        }

    def post_data(self):
        return {
            "telegram_id": self.telegram_id,
            "chat_id": self.chat_id,
            "first_name": self.first_name,
            "last_name": self.last_name
        }
