from django.contrib import admin
from .models import (TelegramUser, Subscriber, 
                     TrainingProgram, Training, Exercise, Approach)

admin.site.register(Subscriber)
admin.site.register(Exercise)
admin.site.register(Approach)


admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_filter = ['difficulty']

class TrainingInline(admin.TabularInline):
    model = Training
    fields = ['name', 'difficulty']
    extra = 0


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    fields = ['telegram_id', ('first_name', 'last_name'), 'balance']


@admin.register(TrainingProgram)
class TrainingProgramAdmin(admin.ModelAdmin):
    inlines = [TrainingInline]
