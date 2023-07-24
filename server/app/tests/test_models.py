from django.test import TestCase
from app.models import TelegramUser, Subscriber


class UserCreationTestCase(TestCase):
    def setUp(self):
        self.valid_data = {
            "telegram_id": "45373Yrteb",
            "chat_id": "8479648923409Ht87482-&*bbdj54673"
        }
        self.model = TelegramUser

    def test_user_creation(self):
        pre_count = self.model.objects.count()
        TelegramUser.objects.create_user(**self.valid_data)
        self.assertEqual(pre_count + 1, TelegramUser.objects.count())

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


class SubscriberCreationTestCase(TestCase):
    def setUp(self):
        self.model = Subscriber
        self.telegram_user = TelegramUser.objects.create_user(
            telegram_id="45373Yrteb",
            chat_id="8479648923409Ht87482-&*bbdj54673"
        )

    def test_subscriber_belongs_user(self):
        subscriber = self.model.objects.create(telegram_user=self.telegram_user)
        self.assertEqual(subscriber, self.telegram_user.subscriber)
