from django.contrib import admin
from .models import Weather
admin.site.register(Weather)
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from celery import Celery
# admin site에 models를 표시하도록함

def create_periodic_task():
    schedule, created = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='0',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*'
    )
    
    task, created = PeriodicTask.objects.get_or_create(
        name='delete_all_data',
        defaults={
            'task': 'myapp.tasks.delete_all_data',
            'crontab': schedule
        }
    )
    
    if not created:
        task.crontab = schedule
        task.save()

    
