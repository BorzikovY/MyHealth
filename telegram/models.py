from datetime import timedelta

import jwt
import re

from dataclasses import dataclass
from typing import List, Callable

from messages import (
    program_message,
    user_message,
    nutrition_message,
    portion_message,
    training_message,
    subscriber_message,
    approach_message,
    exercise_message,
)
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

    def __post_init__(self):
        self.message = portion_message.format(
            name=self.name,
            calories=self.calories,
            proteins=self.proteins,
            fats=self.fats,
            carbs=self.carbs,
            description=self.description
        )

    def filter(self, data: dict):
        if data.get("nutrition_id"):
            return data["nutrition_id"] == self.sport_nutrition
        return True

    id: int
    name: str
    description: str
    calories: int
    proteins: float
    fats: float
    carbs: float
    sport_nutrition: int


@dataclass
class Nutrition:

    def __post_init__(self):
        self.message = nutrition_message.format(
            name=self.name,
            dosages=self.dosages,
            use=self.use,
            contraindications=self.contraindications,
            description=self.description
        )

    id: int
    name: str
    description: str
    dosages: str
    use: str
    price: float
    contraindications: str


@dataclass
class Exercise:

    def __post_init__(self):
        self.message = exercise_message.format(
            name=self.name,
            description=self.description,
            image=self.image,
            video=self.video
        )

    name: str
    description: str
    image: str
    video: str


@dataclass
class Approach:

    @staticmethod
    def convert_time(time: str | None):
        if time is not None:
            _, minutes, seconds = [int(t) for t in time.split(":")]
            return f"{minutes}м {seconds}с"
        return "-"

    @staticmethod
    def number_prefix(number: int) -> str:
        if number:
            end = int(str(number)[-1])
            if end in range(2, 5) and number not in range(12, 15):
                return "раза"
        return "раз"

    def __post_init__(self):
        self.exercise = Exercise(**self.exercise)
        self.message = approach_message.format(
            time=self.convert_time(self.time),
            query_place=self.query_place,
            repetition_count=self.repetition_count,
            repetition_count_prefix=self.number_prefix(self.repetition_count),
            amount=self.amount,
            amount_prefix=self.number_prefix(self.amount),
            rest=self.convert_time(self.rest),
            exercise=self.exercise.message
        )

    id: int
    query_place: int
    time: timedelta
    repetition_count: int
    amount: int
    rest: timedelta
    training: int
    exercise: Exercise


@dataclass
class TrainingProgramGroup:
    name: str
    description: str


@dataclass
class Training:

    def __post_init__(self):
        self.message = training_message.format(
            name=self.name,
            difficulty=self.difficulty,
            time=self.time,
            approach_count=self.approach_count,
            description=self.description
        )

    def filter(self, data: dict):
        if data.get("program_id"):
            return data["program_id"] in self.training_programs
        return True

    id: str
    name: str
    description: str
    difficulty: int
    time: str
    approach_count: int
    training_programs: List[int]


@dataclass
class TrainingProgram:

    @staticmethod
    def convert_time(time: str | None):
        if time is not None:
            minutes = timedelta(seconds=float(time)).total_seconds() // 60
            return f"{int(minutes // 60)}ч {int(minutes % 60)}м"
        return "-"

    @property
    def week_prefix(self) -> str:
        if self.weeks:
            end = int(str(self.weeks)[-1])
            if end == 1 and self.weeks != 11:
                return "неделя"
            elif end in range(2, 5) and self.weeks not in range(12, 15):
                return "недели"
        return "недель"

    def __post_init__(self):
        difficulty_icon = "💪️" if self.difficulty <= 3 else "🦾️"
        group_name = self.group.name if self.group else "Общая подготовка"
        self.message = program_message.format(
            name=self.name, group_name=group_name,
            image=self.image,
            difficulty=self.difficulty,
            difficulty_icon=difficulty_icon,
            weeks=self.weeks,
            week_prefix=self.week_prefix,
            training_count=self.training_count,
            avg_training_time=self.convert_time(self.avg_training_time),
            description=self.description
        )

    def filter(self, data: dict):
        first_filter = DataFilter.filter(data.get("difficulty"), data_class=float)
        second_filter = DataFilter.filter(data.get("weeks"), data_class=int)
        return first_filter(self.difficulty) and second_filter(self.weeks)

    id: int
    name: str
    description: str
    image: str
    weeks: int
    price: float
    group: TrainingProgramGroup
    avg_training_time: timedelta
    training_count: int
    difficulty: float


@dataclass
class Subscriber:

    @property
    def age_prefix(self) -> str:
        if self.age:
            end = int(str(self.age)[-1])
            if end == 1:
                return "год"
            elif end in range(2, 5):
                return "года"
        return "лет"

    @property
    def gender_icon(self) -> str:
        '''Возвращает иконку, соответствующую гендеру'''
        if self.gender == "male":
            return "👨"
        elif self.gender == "female":
            return "👩️"
        return "🚁️"
    
    @property
    def is_kfc_valid(self) -> bool:
        '''Проверяет наличие данных, необходимых для подсчета дневной нормы калорий'''
        return all([self.age, self.height, self.weight]) and (self.gender in ['female', 'male'])
    
    @property
    def water_norm(self) -> float:
        '''Возвращает суточную норму воды'''
        if self.weight:
            return (self.weight*30)/1000
        return "?"
    
    @property
    def bmi(self) -> str:
        '''Возвращает индекс массы тела и его расшифровку'''
        if self.weight and self.height:
            bmi = round(self.weight/(0.0001*self.height**2), 1)
            if bmi < 18.5:
                return f'{bmi} - дефицит массы тела'
            elif 18.5 <= bmi <= 24.9:
                return f'{bmi} - нормальный вес'
            elif 25 <= bmi <= 30:
                return f'{bmi} - избыточный вес'
            elif bmi > 30:
                return f'{bmi} - ожирение'
        return "?"

    def __post_init__(self):
        self.message = subscriber_message.format(
            age=self.age if self.age is not None else "?",
            age_prefix=self.age_prefix,
            height=self.height if self.height is not None else "?",
            weight=self.weight if self.weight is not None else "?",
            gender_icon=self.gender_icon,
            water_norm=self.water_norm,
            bmi=self.bmi
        )

    telegram_id: int
    age: int
    height: float
    weight: float
    training_program: int = None
    sport_nutrition: int = None
    gender: str = 'helicopter'


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
        if self.subscriber:
            self.subscriber = Subscriber(**self.subscriber)

    telegram_id: str
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
