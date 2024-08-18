# app/tasks.py
from config.celery import app
from .models import Weather
from datetime import datetime, timedelta
import json,requests
from django.db import IntegrityError
from django.utils import timezone
import math
from decouple import config
from .calculations import convert_to_xy

GOOGLE_API_KEY=config('GOOGLE_API')
WEATHER_API_KEY=config('WEATHER_API')

# 날씨 데이터 API에 요청
def fetch_weather_data(nx, ny, base_date, base_time):
    url = (
        f"http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
        f"?serviceKey={WEATHER_API_KEY}&numOfRows=100&pageNo=1&dataType=json"
        f"&base_date={base_date}&base_time={base_time}&nx={nx}&ny={ny}"
    )
    try:
        response = requests.get(url, verify=True)
        response.raise_for_status()  # raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

# celery 함수
@app.task()
def task_add(lat,lon,base_date,base_time):
    if lat is None or lon is None:
        return "Failed to get location!"
    nx, ny = convert_to_xy(lon,lat)
    
    res = fetch_weather_data(nx, ny, base_date, base_time)
    if res is None:
        return "Failed to fetch weather data!"
    
    if res['response']['header']['resultCode'] == '00':  # 성공 코드 확인
        informations = {}
        for items in res['response']['body']['items']['item']:
            cate = items['category']
            fcstTime = items['fcstTime']
            fcstValue = items['fcstValue']
            if fcstTime not in informations:
                informations[fcstTime] = {}
            informations[fcstTime][cate] = fcstValue

        weather_data = {
            'date_time': f"{base_date} {base_time}",
            'location': f"{nx},{ny}",
            'data': informations
        }
        try:
            save_weather_data(weather_data)
        except IntegrityError:
            return "Duplicated field of Database!"
    else: 
        print(f"Error fetching data: {res['response']['header']['resultMsg']}")
    return "Success with celery"

# 날씨 데이터를 장고db에 저장하는 함수
def save_weather_data(weather_data):
        Weather.objects.create(
            date_time=weather_data['date_time'],
            location=weather_data['location'],
            data=weather_data['data']
        )

# 날씨 데이터를 자정에 전일 데이터를 모두 삭제하고, 초기 데이터를 하나 생성하는 함수
@app.task()
def delete_all_data():
    Weather.objects.all().delete()
    return f"Deleted all weather data at {timezone.now()}"

