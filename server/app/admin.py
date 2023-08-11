"""import module that register models"""
from datetime import timedelta
from typing import Iterable

from django.contrib import admin

from app.models import (
    TelegramUser,
    Subscriber,
    SportNutrition,
    Portion,
    TrainingProgram,
    Training,
    Exercise,
    Approach,
)
from app.forms import TelegramUserChangeForm

admin.register(Subscriber)
admin.register(Exercise)
admin.register(Approach)
admin.register(TrainingProgram)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    """
    Telegram user Admin panel
    """

    form = TelegramUserChangeForm
    model = TelegramUser
    list_display = (
        "telegram_id",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
    )

    def get_readonly_fields(self, request, obj=None) -> Iterable:
        if obj is not None:
            return ("chat_id",)
        return super(  # pylint: disable=super-with-arguments
            TelegramUserAdmin, self
        ).get_readonly_fields(request, obj)

    fieldsets = (
        (None, {"fields": ("telegram_id", "balance", "first_name", "last_name")}),
        (
            "Permissions",
            {"fields": ("is_staff", "is_active", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "telegram_id",
                    "chat_id",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    """
    Training program Admin panel
    """

    list_display = ("name", "training_count", "difficulty", "avg_training_time")

    def training_count(self, instance: TrainingProgram) -> int:
        """

        @param instance:
        @return: amount of training
        """
        return instance.training_count

    training_count.short_description = "Кол-во тренировок"

    def difficulty(self, instance: TrainingProgram) -> float:
        """

        @param instance:
        @return: average difficulty of all trainings
        """
        return instance.difficulty

    difficulty.short_description = "Сложность"

    def avg_training_time(self, instance: TrainingProgram) -> timedelta | None:
        """

        @param instance:
        @return: average duration of all trainings
        """
        return instance.avg_training_time

    avg_training_time.short_description = "Среднее время одной тренировки"


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    """
    Training Admin panel
    """

    list_display = ("name", "difficulty", "approach_count", "time")
    list_filter = ["difficulty"]

    def approach_count(self, instance: Training) -> int:
        """

        @param instance:
        @return: amount of exercises
        """
        return instance.approach_count

    approach_count.short_description = "Кол-во упражнений"

    def time(self, instance: Training) -> timedelta:
        """

        @param instance:
        @return: training time
        """
        return instance.time

    time.short_description = "Время"


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """
    Subscriber Admin panel
    """

    list_display = ("telegram_user", "gender", "is_adult")

    def is_adult(self, instance: Subscriber) -> bool | None:
        """
        age is over 18 or not
        @param instance:
        @return: bool
        """
        return instance.is_adult

    is_adult.boolean = True
    is_adult.short_description = "Взрослый"


@admin.register(Approach)
class ApproachAdmin(admin.ModelAdmin):
    """
    Approach Admin panel
    """

    list_display = (
        "query_place", "training",
        "exercise", "time",
        "rest", "repetition_count", "amount"
    )

    list_display_links = ["query_place", "training"]


class ApproachInline(admin.TabularInline):
    """
    Approach Tabular inline
    """

    model = Approach
    extra = 1


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    """
    Exercise Admin panel
    """

    list_display = ("name", "image", "video")
    inlines = [
        ApproachInline,
    ]


@admin.register(SportNutrition)
class SportNutritionAdmin(admin.ModelAdmin):
    """
    Sport nutrition Admin panel
    """

    list_display = ("name", "dosages", "use")


@admin.register(Portion)
class PortionAdmin(admin.ModelAdmin):
    """
    Portion Admin panel
    """

    list_display = ("name", "calories", "proteins", "fats", "carbs")
