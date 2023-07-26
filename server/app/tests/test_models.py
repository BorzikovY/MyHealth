from datetime import timedelta

from django.test import TestCase, SimpleTestCase
from app.models import TelegramUser, Subscriber, TrainingProgram, Training, Exercise, Approach, SportNutrition, Portion, \
    TrainingProgramGroup


class UserCreationTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "telegram_id": "45373Yrteb",
            "chat_id": "8479648923409Ht87482-&*bbdj54673"
        }
        self.model = TelegramUser


    def test_no_telegram_id_user_creation(self):
        self.valid_data["telegram_id"], error = None, None
        try:
            TelegramUser.objects.create_user(**self.valid_data)
            self.assertNotEqual(error, None)
        except ValueError as error:
            self.assertNotEqual(error, None)

    def test_no_chat_id_user_creation(self):
        self.valid_data["chat_id"], error = None, None
        try:
            TelegramUser.objects.create_user(**self.valid_data)
            self.assertNotEqual(error, None)
        except ValueError as error:
            self.assertNotEqual(error, None)

    def test_with_balance_user_creation(self):
        self.valid_data["balance"], error = 100.00, None
        try:
            TelegramUser.objects.create_user(**self.valid_data)
            self.assertNotEqual(error, None)
        except ValueError as error:
            self.assertNotEqual(error, None)


class UserDataTestCase(TestCase):
    def setUp(self):
        self.model = Subscriber
        self.valid_data = {
            "telegram_id": "45373Yrteb",
            "chat_id": "8479648923409Ht87482-&*bbdj54673"
        }
        self.telegram_user = TelegramUser.objects.create_user(
            **self.valid_data
        )

    def test_subscriber_belongs_user(self):
        subscriber = self.model.objects.create(telegram_user=self.telegram_user)
        self.assertEqual(subscriber, self.telegram_user.subscriber)

    def test_user_valid_chat_id(self):
        chat_id = self.valid_data.pop("chat_id")
        self.assertEqual(self.telegram_user.check_chat_id(chat_id), True)

    def test_user_invalid_password(self):
        chat_id = self.valid_data.pop("chat_id") + "invalid_string"
        self.assertEqual(self.telegram_user.check_chat_id(chat_id), False)


class ModelCreationMetaCase(type):

    __instances__ = []

    def __new__(cls, name, bases, kwargs):
        for index, (model, data) in enumerate(kwargs.get("__models__", {}).items()):
            test_case = cls.test(model, data=data)
            kwargs[f"test_{index + 1}_{model.__name__}_creation"] = test_case
        return super(ModelCreationMetaCase, cls).__new__(cls, name, bases, kwargs)

    @classmethod
    def test(cls, model, **kwargs):
        def wrapper(*args):
            for instance in cls.__instances__[:len(cls.__instances__)]:
                instance.save()
            pre_count = model.objects.count()
            obj = model.objects.create(**kwargs["data"])
            cls.__instances__.append(obj)
            assert pre_count + 1 == model.objects.count()
        return wrapper


class ModelCreationTestCase(TestCase, metaclass=ModelCreationMetaCase):

    __models__ = {
        TelegramUser: {"id": 1, "telegram_id": "123", "chat_id": "123"},
        Subscriber: {"id": 1, "telegram_user_id": 1},
        TrainingProgramGroup: {
            "id": 1,
            "name": "Name",
            "description": "Description"
        },
        TrainingProgram: {
            "id": 1,
            "name": "Name",
            "description": "Description",
            "weeks": 12,
            "group_id": 1
        },
        Training: {
            "id": 1,
            "name": "Name",
            "difficulty": 3.
        },
        Exercise: {
            "id": 1,
            "name": "Name",
            "description": "Description",
        },
        Approach: {
            "id": 1,
            "time": timedelta(minutes=4),
            "repetition_count": 23,
            "rest": timedelta(seconds=30),
            "training_id": 1,
            "exercise_id": 1
        },
        SportNutrition: {
            "id": 1,
            "name": "Name",
            "description": "Description",
            "dosages": "",
            "use": ""
        },
        Portion: {
            "id": 1,
            "name": "Name",
            "description": "Description",
            "calories": 0,
            "fats": 0,
            "carbs": 0,
            "proteins": 100_000,
            "sport_nutrition_id": 1
        }
    }
