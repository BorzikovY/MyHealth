from datetime import timedelta

import jwt

from dataclasses import dataclass
from typing import List

from settings import config, SECRET_KEY


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

    telegram_id: str
    id: int = None
    chat_id: str = config.get("chat_id")
    access: str = ''
    refresh: str = ''
    first_name: str = ''
    last_name: str = ''
    balance: float = 0
    subscriber: Subscriber = None

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
