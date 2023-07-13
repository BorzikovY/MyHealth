from django.contrib import admin

from app.models import (TelegramUser, Subscriber,
                        TrainingProgram, Training, Exercise, Approach)
from app.forms import TelegramUserChangeForm, TelegramUserCreationForm


admin.register(Subscriber)
admin.register(Exercise)
admin.register(Approach)
admin.register(TrainingProgram)


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_filter = ['difficulty']

# class TrainingInline(admin.TabularInline):
#     model = Training
#     fields = ['name', 'difficulty']
#     extra = 0


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    add_form = TelegramUserCreationForm
    form = TelegramUserChangeForm
    model = TelegramUser
    list_display = ("telegram_id", "first_name", "last_name", "is_superuser", "is_staff")
    fieldsets = (
        (None, {"fields": ("telegram_id", "chat_id")}),
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


# @admin.register(TrainingProgram)
# class TrainingProgramAdmin(admin.ModelAdmin):
#     # inlines = [TrainingInline]
    
