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
    def test_create_token_valid_user(self):
        self.client.post(
            reverse('user'),
            data=json.dumps(self.valid_user),
            content_type='application/json'
        )
        response = self.client.post(
            reverse('token'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_token_invalid_user(self):
        response = self.client.post(
            reverse('token'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
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
        self.token = self.client.post(
            reverse('token'),
            data=json.dumps(dict(itertools.islice(self.valid_user.items(), 2))),
            content_type='application/json'
        ).json()
        
    def test_get_user_valid_token(self):
        response = self.client.get(
            reverse('user'),
            headers=self.token,
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
