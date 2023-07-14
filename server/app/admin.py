from django.contrib import admin

from app.models import (TelegramUser, Subscriber, SportNutrition, Portion,
                        TrainingProgram, Training, Exercise, Approach)
from app.forms import TelegramUserChangeForm, TelegramUserCreationForm


admin.register(Subscriber)
admin.register(Exercise)
admin.register(Approach)
admin.register(TrainingProgram)


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    add_form = TelegramUserCreationForm
    form = TelegramUserChangeForm
    model = TelegramUser
    readonly_fields = ("chat_id",)
    list_display = ("telegram_id", "first_name", "last_name", "is_superuser", "is_staff")
    fieldsets = (
        (None, {"fields": ("telegram_id", "chat_id", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "telegram_id", "chat_id", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
        ),
    )


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "training_count", "difficulty", "avg_training_time")

    def training_count(self, instance):
        return instance.training_count
    training_count.short_description = "Кол-во тренировок"

    def difficulty(self, instance):
        return instance.difficulty
    difficulty.short_description = "Сложность"

    def avg_training_time(self, instance):
        return instance.avg_training_time
    avg_training_time.short_description = "Среднее время одной тренировки"


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "approach_count", "time")
    list_filter = ['difficulty']

    def approach_count(self, instance):
        return instance.approach_count
    approach_count.short_description = "Кол-во упражнений"

    def time(self, instance):
        return instance.time
    time.short_description = "Время"


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("telegram_user", "gender", "is_adult")

    def is_adult(self, instance):
        return instance.is_adult
    is_adult.boolean = True
    is_adult.short_description = "Взрослый"


@admin.register(Approach)
class ApproachAdmin(admin.ModelAdmin):
    list_display = ("training", "exercise", "time", "rest", "repetition_count")


class ApproachInline(admin.TabularInline):
    model = Approach
    extra = 1


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "approach_time", "approach_rest")
    inlines = [ApproachInline,]

    def approach_time(self, instance):
        time = Approach.objects.filter(exercise_id=instance.id).values("time")
        if time:
            return time[0]["time"]
    approach_time.short_description = "Время выполнения"

    def approach_rest(self, instance):
        time = Approach.objects.filter(exercise_id=instance.id).values("rest")
        if time:
            return time[0]["rest"]
    approach_rest.short_description = "Время отдыха"


@admin.register(SportNutrition)
class SportNutritionAdmin(admin.ModelAdmin):
    list_display = ("name", "dosages", "use")


@admin.register(Portion)
class PortionAdmin(admin.ModelAdmin):
    list_display = ("name", "calories")
