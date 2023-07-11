from datetime import time

from django.contrib.auth.models import AbstractUser
from django.db import models


class TelegramUser(AbstractUser):
    telegram_id = models.IntegerField(verbose_name="Telegram id", unique=True)
    first_name = models.CharField(verbose_name="Имя", max_length=32)
    last_name = models.CharField(verbose_name="Фамилия", max_length=64)
    balance = models.FloatField(verbose_name="Баланс", default=0., blank=True)


class Subscriber(models.Model):
    GENDERS = (
        ("male", "мужик"),
        ("female", "баба"),
        ("helicopter", "вертолёт")
    )
    telegram_user = models.OneToOneField(TelegramUser, verbose_name="Пользователь",
                                         on_delete=models.CASCADE, related_name="subscriber")
    gender = models.CharField(verbose_name="Гендер", default="helicopter")
    age = models.SmallIntegerField(verbose_name="Возраст")
    height = models.FloatField(verbose_name="Рост")
    weight = models.FloatField(verbose_name="Вес")


class TrainingProgram(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.CharField(verbose_name="Описание", max_length=256)
    image = models.FileField(verbose_name="Изображение", upload_to="./")
    weeks = models.SmallIntegerField(verbose_name="Кол-во недель")
    trainings = models.ManyToManyField("Training", verbose_name="Тренировки",
                                       related_query_name="training_programs")

    @property
    def avg_training_time(self) -> time:
        return

    @property
    def training_count(self) -> int:
        return

    @property
    def difficulty(self) -> str:
        return


class Training(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.CharField(verbose_name="Описание", max_length=256)
    difficulty = models.FloatField(verbose_name="Сложность")
    training_programs = models.ManyToManyField(TrainingProgram, verbose_name="Тренировочные программы",
                                               related_query_name="trainings")

    @property
    def time(self) -> time:
        return

    @property
    def exercise_count(self) -> int:
        return


class Exercise(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.CharField(verbose_name="Описание", max_length=256)
    image = models.FileField(verbose_name="Изображение", upload_to="./")
    video = models.FileField(verbose_name="Видео", upload_to="./")
    training = models.ForeignKey(Training, verbose_name="Тренировка", related_name="approach", on_delete=models.CASCADE)


class Approach(models.Model):
    time = models.TimeField(verbose_name="Время выполнения")
    repetition_count = models.SmallIntegerField(verbose_name="Кол-во повторений")
    rest = models.TimeField(verbose_name="Время отдыха")
    exercise = models.OneToOneField(Exercise, verbose_name="Упражнение",
                                    on_delete=models.CASCADE, related_name="approach")



