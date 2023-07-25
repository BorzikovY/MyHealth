from abc import abstractmethod
from random import randint

from django.contrib.auth.models import Group
from django.urls import include, path, reverse
import json
import itertools
from rest_framework import status
from rest_framework.test import APITestCase
from app.models import Subscriber, TelegramUser, Training, TrainingProgram, Exercise, SportNutrition


class BaseAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.valid_user = {
            "telegram_id": "string",
            "chat_id": "string",
            "first_name": "string",
            "last_name": "string",
        }
        self.invalid_user = {
            "telegram_id": 1,
            "chat_id": None,
            "first_name": "string",
            "last_name": "string",
        }


class UserCreateTests(BaseAPITestCase):
    def test_create_valid_user(self):
        response = self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TelegramUser.objects.count(), 1)
        self.assertEqual(TelegramUser.objects.get().telegram_id, 'string')

    def test_create_invalid_user(self):
        response = self.client.post(
            reverse('user'),
            data=json.dumps(self.invalid_user),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TokenTests(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )

    def test_create_token_valid_user(self):
        response = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_user(self):
        response = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.invalid_user.items(), 2))),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_valid_token(self):
        token = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        ).json().get('refresh')
        response = self.client.post(
            reverse('token_refresh'),
            data=json.dumps({'refresh': '{token}'.format(token=token)}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_invalid_token(self):
        response = self.client.post(
            reverse('token_refresh'),
            data=json.dumps({'refresh': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_without_token(self):
        response = self.client.post(
            reverse('token_refresh')
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserTests(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        response = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        ).json()
        self.token = response.get('access')

    def test_get_user_valid_token(self):
        response = self.client.get(
            reverse('user'),
            headers={'Authorization': "Bearer {token}".format(token=self.token)},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_user_invalid_token(self):
        response = self.client.get(
            reverse('user'),
            headers={'Authorization': ''},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_without_token(self):
        response = self.client.get(
            reverse('user')
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_valid_user(self):
        response = self.client.put(
            reverse('user'),
            headers={'Authorization': "Bearer {token}".format(token=self.token)},
            data=json.dumps({'first_name': '', 'last_name': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(TelegramUser.objects.count(), 1)
        self.assertEqual(TelegramUser.objects.get().first_name, '')

    # def test_reset_invalid_user(self):
    #     response = self.client.put(
    #         reverse('user'),
    #         headers={'Authorization': "Bearer {token}".format(token=self.token)},
    #         data=json.dumps({'':''}),
    #         content_type='application/json'
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_valid_user_invalid_token(self):
        response = self.client.put(
            reverse('user'),
            headers={'Authorization': "Bearer "},
            data=json.dumps({'first_name': '', 'last_name': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reset_valid_user_without_token(self):
        response = self.client.put(
            reverse('user'),
            data=json.dumps({'first_name': '', 'last_name': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriberCreateTests(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        self.token = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        ).json().get('access')

    def test_create_subscriber_valid_token(self):
        response = self.client.post(
            reverse('subscribe'),
            headers={'Authorization': "Bearer {token}".format(token=self.token)},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscriber.objects.count(), 1)
        self.assertEqual(TelegramUser.objects.get().age, None)

    def test_create_subscriber_invalid_token(self):
        response = self.client.post(
            reverse('subscribe'),
            headers={'Authorization': ""},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_subscriber_valid_token(self):
        response = self.client.post(
            reverse('subscribe'),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriberTests(BaseAPITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )

        self.token = self.client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        ).json().get('access')
        self.client.post(
            reverse('subscribe'),
            headers={'Authorization': "Bearer {token}".format(token=self.token)},
            content_type='application/json'
        )

    def test_get_subscriber_valid_token(self):
        response = self.client.get(
            reverse('subscribe'),
            headers={'Authorization': "Bearer {token}".format(token=self.token)},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_subscriber_invalid_token(self):
        response = self.client.get(
            reverse('subscribe'),
            headers={'Authorization': ""},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def get_subscriber_without_token(self):
        response = self.client.get(
            reverse('subscribe'),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    ...


class SubscriberRegisterMixin:
    def get_token(self, client, data):
        user = TelegramUser.objects.create_user(**data)
        group = Group.objects.create(name="Staff")
        user.groups_set = [group]
        response = client.post(
            reverse('token_obtain'),
            data=json.dumps({"telegram_id": user.telegram_id, "chat_id": user.chat_id}),
            content_type='application/json'
        ).json()
        return response.get('access')

    def subscribe_user(self, client, data):
        token = self.get_token(client, data)
        client.post(
            reverse('subscribe'),
            headers={"Authorization": f"Bearer {token}"},
            content_type='application/json'
        )
        return {"Authorization": f"Bearer {token}"}


class ApiListTest(SubscriberRegisterMixin):

    client = None
    valid_user = None
    reverse_name = None

    @abstractmethod
    def get_data(self, index):
        pass

    def setUp(self, model) -> None:
        self.model = model
        self.headers = self.subscribe_user(self.client, self.valid_user)
        self.objects, self.url = [], reverse(self.reverse_name)
        for i in range(randint(3, 7)):
            instance = self.model.objects.create(
                **self.get_data(i)
            )
            self.objects.append(instance)


class ProgramListTest(BaseAPITestCase, ApiListTest):

    def get_data(self, index):
        return {
            "name": f"Title_{index}",
            "description": "Description",
            "weeks": randint(4, 12)
        }

    def setUp(self) -> None:
        BaseAPITestCase.setUp(self)
        self.reverse_name = "program-list"
        ApiListTest.setUp(self, TrainingProgram)

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        ).json()
        self.assertEqual(len(response), self.model.objects.count())
