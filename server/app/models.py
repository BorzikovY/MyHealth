import hashlib
from datetime import timedelta
from typing import List

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg, F, ExpressionWrapper, Func, Sum, Count

from app.managers import TelegramUserManager


class TelegramUser(AbstractUser):
    username, password, email = None, None, None
    USERNAME_FIELD = "telegram_id"

    REQUIRED_FIELDS = ["chat_id",]

    objects = TelegramUserManager()

    telegram_id = models.CharField(verbose_name="Telegram id", unique=True, max_length=32)
    chat_id = models.CharField(verbose_name="Chat id", unique=True, max_length=128)
    first_name = models.CharField(verbose_name="Имя", max_length=32, null=True, blank=True)
    last_name = models.CharField(verbose_name="Фамилия", max_length=64, null=True, blank=True)
    balance = models.FloatField(verbose_name="Баланс", default=0., blank=True, null=True)

    @classmethod
    def encode_chat_id(cls, string: str) -> str:
        hash_string = hashlib.sha512(string.encode("utf-8"))
        return hash_string.hexdigest()

    def set_chat_id(self, string: str):
        self.chat_id = self.encode_chat_id(string)

    def check_chat_id(self, string: str) -> bool:
        return self.encode_chat_id(string) == self.chat_id

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}"
        return f"Telegram user, id: {self.telegram_id}"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


def gender_length(genders: List) -> int:
    sorted_genders = sorted([item[0] for item in genders], key=lambda item: len(item))
    return len(sorted_genders[-1])


class Subscriber(models.Model):

    GENDERS = (
        ("male", "мужчина"),
        ("female", "женщина"),
        ("helicopter", "вертолёт")
    )
    telegram_user = models.OneToOneField(TelegramUser, verbose_name="Пользователь",
                                         on_delete=models.CASCADE, related_name="subscriber")
    gender = models.CharField(choices=GENDERS, verbose_name="Гендер",
                              default="helicopter", max_length=gender_length(GENDERS))
    age = models.PositiveSmallIntegerField(verbose_name="Возраст")
    height = models.FloatField(verbose_name="Рост", validators=[MinValueValidator(1), MaxValueValidator(3)])
    weight = models.FloatField(verbose_name="Вес", validators=[MinValueValidator(20), MaxValueValidator(200)])

    def __str__(self):
        return str(self.telegram_user)

    @property
    def is_adult(self) -> bool:
        return self.age >= 18

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'


class TrainingProgram(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    image = models.FileField(verbose_name="Изображение", upload_to="images/program")
    weeks = models.SmallIntegerField(verbose_name="Кол-во недель", validators=[MinValueValidator(1)])
    trainings = models.ManyToManyField("Training", verbose_name="Тренировки",
                                       related_query_name="training_programs")
    sport_nutrition = models.ForeignKey("SportNutrition", verbose_name="Спортивные добавки",
                                        related_name="training_program", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.name}, сложность: {self.difficulty}"

    @property
    def avg_training_time(self) -> timedelta:
        trainings = Training.objects.filter(
            training_programs__id=self.id
        )
        output = trainings.aggregate(
            time=Sum(F('approach__time') + F('approach__rest'))
        )
        return output.get("time") / len(trainings)

    @property
    def training_count(self) -> int:
        count = Training.objects.filter(
            training_programs__id=self.id
        ).count()
        return count

    @property
    def difficulty(self) -> str:
        queryset = Training.objects.filter(
            training_programs__id=self.id
        ).aggregate(Avg("difficulty"))
        return queryset.get("difficulty__avg")

    class Meta:
        verbose_name = 'Тренировочная программа'
        verbose_name_plural = 'Тренировочные программы'


class Training(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    difficulty = models.FloatField(verbose_name="Сложность", 
                                   validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f"{self.name}, сложность: {self.difficulty}"

    @property
    def time(self) -> timedelta:
        output = Approach.objects.filter(
            training_id=self.id
        ).aggregate(
            time=Sum(F('time') + F('rest'))
        )
        return output.get("time")

    @property
    def approach_count(self) -> int:
        count = Approach.objects.filter(training_id=self.id).count()
        return count
    
    class Meta:
        verbose_name = 'Тренировка'
        verbose_name_plural = 'Тренировки'


class Exercise(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    image = models.FileField(verbose_name="Изображение", upload_to="images/exercise")
    video = models.FileField(verbose_name="Видео", upload_to="videos/exercise")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'


class Approach(models.Model):
    time = models.DurationField(verbose_name="Время выполнения")
    repetition_count = models.SmallIntegerField(verbose_name="Кол-во повторений",
                                                validators=[MinValueValidator(1)])
    rest = models.DurationField(verbose_name="Время отдыха")
    training = models.ForeignKey(Training, verbose_name="Тренировка",
                                 related_name="approach", on_delete=models.CASCADE, null=True)
    exercise = models.ForeignKey(Exercise, verbose_name="Упражнение",
                                 related_name="approach", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.exercise}, кол-во повторений: {self.repetition_count}"

    class Meta:
        verbose_name = 'Подход'
        verbose_name_plural = 'Подходы'


class SportNutrition(models.Model):
    name = models.CharField(verbose_name="Название", max_length=32)
    description = models.TextField(verbose_name="Описание")
    dosages = models.CharField(verbose_name="Дозировки", max_length=100)
    use = models.CharField(verbose_name="Способ применения", max_length=100)
    contraindications = models.CharField(verbose_name="Противопоказания", max_length=100)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Спортивная добавка'
        verbose_name_plural = 'Спортивные добавки'


class Portion(models.Model):
    name = models.CharField(verbose_name="Название", max_length=32)
    description = models.TextField(verbose_name="Описание")
    calories = models.PositiveSmallIntegerField(verbose_name="Калории")
    proteins = models.FloatField(verbose_name="Белки", validators=[MinValueValidator(0)])
    fats = models.FloatField(verbose_name="Жиры", validators=[MinValueValidator(0)])
    carbs = models.FloatField(verbose_name="Углеводы", validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Порция'
        verbose_name_plural = 'Порции'
