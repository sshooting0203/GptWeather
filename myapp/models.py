from django.db import models

# 기상청 데이터를 이용한 날씨 데이터 모델

class Weather(models.Model):
    date_time = models.CharField(max_length=100,unique=True)  # 예보 날짜와 시간
    location = models.CharField(max_length=100)  # 예보를 내리는 위치
    data = models.JSONField()  # 기상 데이터 (JSON 형식)
    recorded = models.DateTimeField(auto_now_add=True) # 데이터가 기록된 시간

    def __str__(self):
        return f"Weather at {self.location} on {self.date_time}"
