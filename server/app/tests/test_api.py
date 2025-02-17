from abc import abstractmethod
from datetime import timedelta
from random import randint

from django.contrib.auth.models import Group
from django.urls import include, path, reverse
import json
import itertools
from rest_framework import status
from rest_framework.test import APITestCase
from app.models import Subscriber, TelegramUser, Training, TrainingProgram, Exercise, SportNutrition, Approach, Portion


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

    def test_get_subscriber_without_token(self):
        response = self.client.get(
            reverse('subscribe'),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriberRegisterMixin:
    def get_token(self, client, data):
        user = TelegramUser.objects.create_user(**data)
        group = Group.objects.create(name="Staff")
        group.user_set.add(user)
        group.save()
        response = client.post(
            reverse('token_obtain'),
            data=json.dumps(dict(itertools.islice(data.items(), 2))),
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


class ApiListTest(BaseAPITestCase, SubscriberRegisterMixin):
    model = None

    @abstractmethod
    def get_data(self):
        pass

    def create_instance(self):
        data = self.get_data()
        if related := data.get("related"):
            data.pop("related")
        instance = self.model.objects.create(
            **data
        )
        if related:
            related_instance = related.get("instance")
            getattr(
                related_instance,
                related.get("back_populated_field")
            ).add(instance)
            related_instance.save()

        return instance

    def setUp(self, reverse_name) -> None:
        BaseAPITestCase.setUp(self)
        self.headers = self.subscribe_user(self.client, self.valid_user)
        self.url = reverse(reverse_name)
        for i in range(randint(3, 7)):
            self.create_instance()


class ProgramListTest(ApiListTest):
    model = TrainingProgram

    def get_data(self):
        return {
            "name": f"Title",
            "description": "Description",
            "weeks": randint(4, 12)
        }

    def setUp(self) -> None:
        super(ProgramListTest, self).setUp("program-list")

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        ).json()
        self.assertEqual(len(response), self.model.objects.count())


class TrainingListTest(ApiListTest):
    model = Training

    def get_data(self):
        return {
            "related": {
                "instance": self.program,
                "back_populated_field": "trainings"
            },
            "name": "Name",
            "difficulty": 3.
        }

    def setUp(self) -> None:
        self.program = ProgramListTest().create_instance()
        super(TrainingListTest, self).setUp("training-list")

    def test_amount(self):
        response = self.client.get(
            f"{self.url}?program_id={self.program.id}",
            headers=self.headers,
            content_type='application/json'
        ).json()
        self.assertEqual(len(response), self.model.objects.count())


class ExerciseListTest(ApiListTest):
    model = Exercise

    def get_data(self):
        return {
            "name": "Name",
            "description": "Description",
        }


class ApproachListTest(ApiListTest):
    model = Approach

    def get_data(self):
        return {
            "time": timedelta(minutes=4),
            "repetition_count": 23,
            "rest": timedelta(seconds=30),
            "training": self.training,
            "exercise": self.exercise
        }

    def setUp(self) -> None:
        training_test = TrainingListTest()
        training_test.program = ProgramListTest().create_instance()
        self.training = training_test.create_instance()
        self.exercise = ExerciseListTest().create_instance()
        super(ApproachListTest, self).setUp("exercise-list")

    def test_amount(self):
        response = self.client.get(
            f"{self.url}?training_id={self.training.id}",
            headers=self.headers,
            content_type='application/json'
        ).json()
        self.assertEqual(len(response), self.model.objects.count())


class SportNutritionListTest(ApiListTest):
    model = SportNutrition

    def get_data(self):
        return {
            "name": "Name",
            "description": "Description",
            "dosages": "",
            "use": ""
        }

    def setUp(self) -> None:
        self.reverse_name = "nutrition-list"
        super(SportNutritionListTest, self).setUp("nutrition-list")

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        )
        self.assertEqual(len(response.json()), self.model.objects.count())


class ApiTest(BaseAPITestCase, SubscriberRegisterMixin):
    model = None

    @abstractmethod
    def get_data(self):
        pass

    def create_instance(self):
        data = self.get_data()
        if related := data.get("related"):
            data.pop("related")
        instance = self.model.objects.create(
            **data
        )
        if related:
            related_instance = related.get("instance")
            setattr(
                related_instance,
                related.get("back_populated_field"),
                instance
            )
            related_instance.save()

        return instance

    def setUp(self, reverse_name, _id) -> None:
        BaseAPITestCase.setUp(self)
        self.headers = self.subscribe_user(self.client, self.valid_user)
        self.url = reverse(reverse_name, args=(_id,))
        self.instance = self.create_instance()


class TrainingProgramTest(ApiTest):
    program_id = 1
    model = TrainingProgram

    def get_data(self):
        return {
            'id': self.program_id,
            "name": f"Title",
            "description": "Description",
            "weeks": randint(4, 12)
        }

    def setUp(self) -> None:
        ApiTest.setUp(self, 'program', self.program_id)

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SportNutritionTest(ApiTest):
    nutrition_id = 1
    model = SportNutrition

    def get_data(self):
        return {
            'id': self.nutrition_id,
            "name": f"Title",
            "description": "Description",
            "dosages": "",
            "use": "",
            "contraindications": "",
            "related": {
                'instance': Portion(
                    name='',
                    description='',
                    calories=1,
                    proteins=0,
                    fats=0,
                    carbs=0
                ),
                "back_populated_field": "sport_nutrition"}
        }

    def setUp(self) -> None:
        ApiTest.setUp(self, 'nutrition', self.nutrition_id)

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ExerciseTest(ApiTest):
    exercise_id = 1
    model = Exercise

    def get_data(self):
        return {
            "name": f"Title",
            "description": "Description",
            "image": "",
            "video": ""
        }

    def setUp(self) -> None:
        ApiTest.setUp(self, 'exercise', self.exercise_id)

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TrainingTest(ApiTest):
    training_id = 1
    model = Training

    def get_data(self):
        return {
            'id': self.training_id,
            "name": f"Title",
            "description": "Description",
            "difficulty": randint(1, 5)
        }

    def setUp(self) -> None:
        ApiTest.setUp(self, 'training', self.training_id)

    def test_amount(self):
        response = self.client.get(
            self.url,
            headers=self.headers,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
