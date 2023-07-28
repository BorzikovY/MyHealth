import jwt

from dataclasses import dataclass
from typing import List

from settings import config, SECRET_KEY


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
