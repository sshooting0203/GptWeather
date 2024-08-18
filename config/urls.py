from django.contrib import admin
from django.urls import path,include
from myapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),  # 메인 페이지
    path('task-status/<str:task_id>/', task_status, name='task_status'), # Celery 작업 상태 확인
    path('save-location/',save_location,name='save_location'),
]

handler404 = 'myapp.views.page_not_found'
