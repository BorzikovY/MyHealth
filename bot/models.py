from dataclasses import dataclass
from typing import List


@dataclass
class TrainingProgramGroup:
    name: str
    description: str


@dataclass
class TrainingProgram:
    name: str
    description: str
    image: str
    weeks: int
    trainings: List[Training]
    group: TrainingProgramGroup


@dataclass
class TelegramUser:
    telegram_id: str
    chat_id: str
    first_name: str = 'Неизвестно'
    last_name: str = 'Неизвестно'
    balance: float = 0


@dataclass
class Subscriber:
    telegram_user: TelegramUser
    gender: str = 'helicopter'
    age: int
    height: float
    weight: float
    training_program: any
    sport_nutrition: any
