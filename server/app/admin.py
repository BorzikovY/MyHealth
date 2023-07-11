from django.contrib import admin
from .models import (TelegramUser, Subscriber, 
                     TrainingProgram, Training, Exercise, Approach)


admin.site.register(TelegramUser)
admin.site.register(Subscriber)
admin.site.register(TrainingProgram)
admin.site.register(Training)
admin.site.register(Exercise)
admin.site.register(Approach)