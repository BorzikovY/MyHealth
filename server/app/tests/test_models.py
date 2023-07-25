from django.test import TestCase, SimpleTestCase
from app.models import TelegramUser, Subscriber


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

    __queries__ = []

    def __new__(cls, name, bases, kwargs):
        for index, (model, data) in enumerate(kwargs.get("__models__", {}).items()):
            commit = True if index != 0 else False
            test_case = cls.test(model, commit, data=data)
            kwargs[f"test_{model.__name__}_creation"] = test_case
        kwargs['setUp'] = cls.setUp()
        return super(ModelCreationMetaCase, cls).__new__(cls, name, bases, kwargs)

    # def setUp(cls):
    #     def wrapper():
    #     for query in cls.__queries__:
    #         query()

    @classmethod
    def test(cls, model, commit=False, **kwargs):
        def wrapper(*args):
            pre_count = model.objects.count()
            query = model.objects.create(**kwargs["data"]).query
            if commit:
                cls.__queries__.append(query)
            assert pre_count + 1 == model.objects.count()
        return wrapper


class ModelCreationTestCase(TestCase, metaclass=ModelCreationMetaCase):

    def setUp(self) -> None:
        return

    __models__ = {
        TelegramUser: {"id": 2, "telegram_id": "123", "chat_id": "123"},
        Subscriber: {"id": 1, "telegram_user_id": 1}
    }
