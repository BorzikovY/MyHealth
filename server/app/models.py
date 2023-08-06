"""
Import modules for annotation and hashing strings
Import modules for describing tables and queries
Import Telegram user manager module
"""
import hashlib
from datetime import timedelta
from typing import List

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, F, Sum

from app.managers import TelegramUserManager


class TelegramUser(AbstractUser):
    """
    Telegram user model
    """

    username, password, email = None, None, None
    USERNAME_FIELD = "telegram_id"

    REQUIRED_FIELDS = [
        "chat_id",
    ]

    objects = TelegramUserManager()

    telegram_id = models.CharField(
        verbose_name="Telegram id", unique=True, max_length=32
    )
    chat_id = models.CharField(verbose_name="Chat id", unique=True, max_length=128)
    first_name = models.CharField(
        verbose_name="Имя", max_length=32, null=True, blank=True
    )
    last_name = models.CharField(
        verbose_name="Фамилия", max_length=64, null=True, blank=True
    )
    balance = models.FloatField(
        verbose_name="Баланс", default=0.0, blank=True, null=True,
        validators=[MinValueValidator(0.)],
    )

    @property
    def cash(self):
        return self.balance

    @cash.setter
    def cash(self, value):
        if value >= 0.:
            self.balance = value
        else:
            raise ValidationError("Balance is below 0")

    @classmethod
    def encode_chat_id(cls, string: str) -> str:
        """
        Hashing chat_id with sha512 algorythm
        @param string:
        @return: hashed chat_id
        """
        hash_string = hashlib.sha512(string.encode("utf-8"))
        return hash_string.hexdigest()

    def set_chat_id(self, string: str) -> None:
        """

        @param string: new chat_id
        @return: None
        """
        self.chat_id = self.encode_chat_id(string)

    def check_chat_id(self, string: str) -> bool:
        """
        Check string is equal to chat_id
        @param string:
        @return: chat_id is valid
        """
        return self.encode_chat_id(string) == self.chat_id

    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}"
        return f"Telegram user, id: {self.telegram_id}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


def gender_length(genders: List) -> int:
    """
    max length of all genders
    @param genders:
    @return: int
    """
    sorted_genders = sorted(
        [item[0] for item in genders],
        key=lambda item: len(item),  # pylint: disable=unnecessary-lambda
    )
    return len(sorted_genders[-1])


class Subscriber(models.Model):
    """
    Subscriber model
    """

    GENDERS = (("male", "мужчина"), ("female", "женщина"), ("helicopter", "вертолёт"))
    telegram_user = models.OneToOneField(
        TelegramUser,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="subscriber",
    )
    gender = models.CharField(
        choices=GENDERS,
        verbose_name="Гендер",
        default="helicopter",
        max_length=gender_length(GENDERS),
        null=True,
        blank=True,
    )
    age = models.PositiveSmallIntegerField(
        verbose_name="Возраст", blank=True, null=True
    )
    height = models.FloatField(
        verbose_name="Рост",
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        blank=True,
        null=True,
    )
    weight = models.FloatField(
        verbose_name="Вес",
        validators=[MinValueValidator(20), MaxValueValidator(200)],
        blank=True,
        null=True,
    )
    training_program = models.ForeignKey(
        "TrainingProgram",
        verbose_name="Тренировочная программа",
        on_delete=models.SET_NULL,
        related_name="subscribers",
        related_query_name="subscriber_set",
        null=True,
        blank=True,
    )
    sport_nutrition = models.ForeignKey(
        "SportNutrition",
        verbose_name="Спортивное питание",
        on_delete=models.SET_NULL,
        related_name="subscribers",
        related_query_name="subscriber_set",
        null=True,
        blank=True
    )

    def __str__(self):
        return str(self.telegram_user)

    @property
    def is_adult(self) -> bool:
        """
        age is over 18 or not
        @return: bool
        """
        if isinstance(self.age, int):
            return self.age >= 18
        return None

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Подписчик"
        verbose_name_plural = "Подписчики"


class TrainingProgramGroup(models.Model):
    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Тренировочная группа"
        verbose_name_plural = "Тренировочные группы"


class TrainingProgram(models.Model):
    """
    Training program model
    """

    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    image = models.FileField(verbose_name="Изображение", upload_to="images/program")
    weeks = models.SmallIntegerField(
        verbose_name="Кол-во недель", validators=[MinValueValidator(1)]
    )
    price = models.FloatField(verbose_name="Цена", default=0.0)
    trainings = models.ManyToManyField(
        "Training",
        verbose_name="Тренировки",
        related_query_name="training_program_set",
        related_name="training_programs",
    )
    group = models.ForeignKey(
        TrainingProgramGroup,
        verbose_name="Тип тренировочной программы",
        related_name="training_programs",
        related_query_name="training_program_set",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name}, сложность: {self.difficulty}"

    @property
    def avg_training_time(self) -> timedelta:
        """
        average training time
        @return: timedelta
        """
        trainings = Training.objects.filter(  # pylint: disable=no-member
            training_program_set=self
        )
        output = trainings.aggregate(
            time=Sum(F("approach_set__time") + F("approach_set__rest"))
        )
        if output.get("time", None) is not None:
            return output.get("time") / len(trainings)
        return 0

    @property
    def training_count(self) -> int:
        """
        training amount
        @return: int
        """
        count = Training.objects.filter(  # pylint: disable=no-member
            training_program_set=self
        ).count()
        return count

    @property
    def difficulty(self) -> float:
        """
        average training difficulty
        @return: float
        """
        queryset = Training.objects.filter(  # pylint: disable=no-member
            training_program_set=self
        ).aggregate(Avg("difficulty"))
        return queryset.get("difficulty__avg", 0)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Тренировочная программа"
        verbose_name_plural = "Тренировочные программы"


class Training(models.Model):
    """
    Training model
    """

    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    difficulty = models.FloatField(
        verbose_name="Сложность",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    def __str__(self):
        return f"{self.name}, сложность: {self.difficulty}"

    @property
    def time(self) -> timedelta:
        """
        sum of all approach time and rest
        @return: timedelta
        """
        output = Approach.objects.filter(  # pylint: disable=no-member
            training_id=self.id  # pylint: disable=no-member
        ).aggregate(time=Sum(F("time") + F("rest")))
        return output.get("time", 0)

    @property
    def approach_count(self) -> int:
        """
        approach amount
        @return: int
        """
        count = Approach.objects.filter(  # pylint: disable=no-member
            training_id=self.id  # pylint: disable=no-member
        ).count()
        return count

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"


class Exercise(models.Model):
    """
    Exercise model
    """

    name = models.CharField(verbose_name="Название", max_length=64)
    description = models.TextField(verbose_name="Описание")
    image = models.FileField(verbose_name="Изображение", upload_to="images/exercise")
    video = models.FileField(verbose_name="Видео", upload_to="videos/exercise")

    def __str__(self):
        return f"{self.name}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"


class Approach(models.Model):
    """
    Approach model
    """

    time = models.DurationField(verbose_name="Время выполнения")
    repetition_count = models.SmallIntegerField(
        verbose_name="Кол-во повторений", validators=[MinValueValidator(1)]
    )
    rest = models.DurationField(verbose_name="Время отдыха")
    training = models.ForeignKey(
        Training,
        verbose_name="Тренировка",
        related_name="approaches",
        related_query_name="approach_set",
        on_delete=models.CASCADE,
        null=True,
    )
    exercise = models.ForeignKey(
        Exercise,
        verbose_name="Упражнение",
        related_name="approaches",
        related_query_name="approach_set",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.exercise}, кол-во повторений: {self.repetition_count}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Подход"
        verbose_name_plural = "Подходы"


class SportNutrition(models.Model):
    """
    Sport nutrition model
    """

    name = models.CharField(verbose_name="Название", max_length=32)
    description = models.TextField(verbose_name="Описание")
    dosages = models.TextField(verbose_name="Дозировки")
    use = models.TextField(verbose_name="Способ применения")
    price = models.FloatField(verbose_name="Цена", default=0.0)
    contraindications = models.TextField(
        verbose_name="Противопоказания",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Спортивная добавка"
        verbose_name_plural = "Спортивные добавки"


class Portion(models.Model):
    """
    Portion model
    """

    name = models.CharField(verbose_name="Название", max_length=32)
    description = models.TextField(verbose_name="Описание")
    calories = models.PositiveSmallIntegerField(verbose_name="Калории")
    proteins = models.FloatField(
        verbose_name="Белки", validators=[MinValueValidator(0)]
    )
    fats = models.FloatField(verbose_name="Жиры", validators=[MinValueValidator(0)])
    carbs = models.FloatField(
        verbose_name="Углеводы", validators=[MinValueValidator(0)]
    )
    sport_nutrition = models.ForeignKey(
        SportNutrition,
        verbose_name="Спортивное питание",
        on_delete=models.CASCADE,
        related_name="portions",
        related_query_name="portion_set",
    )

    def __str__(self):
        return f"{self.name}"

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta data
        """

        verbose_name = "Порция"
        verbose_name_plural = "Порции"
