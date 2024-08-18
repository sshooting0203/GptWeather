from rest_framework.response import Response
from .tasks import task_add
from django.http import HttpResponse
from .models import Weather
from django.utils import timezone
from openai import OpenAI
from typing import List,Dict
from django.shortcuts import render
import os,json,re
from django.http import JsonResponse
from celery.result import AsyncResult
from config.celery import app
from datetime import datetime, timedelta
import logging,time
from decouple import config
from .calculations import convert_to_xy

api_keys = config('OPENAI_API')
logger = logging.getLogger('mysite')

# OPENAI 클라이언트 생성
client = OpenAI(api_key=api_keys)

def ask_chatgpt(messages):
  response = client.chat.completions.create(
    model="gpt-3.5-turbo", messages=messages
  )
  return response.choices[0].message.content

# 날씨 데이터를 파싱하여 해석하는 함수
def parse_weather_data(weather_data: dict) -> Dict[str, List[str]]:
    facts = {}
    pty_map = {"0": "None", "1": "Rain", "2": "Rain/Snow", "3": "Snow", "5": "Raindrop", "6":"Raindrop/A snowflake", "7":"A snowflake"} # 강수형태코드
    sky_map = {"1":"Sunny", "3":"Partly Cloudy", "4": "Cloudy"} # 하늘형태코드
    # 필드에 대한 정보를 딕셔너리로 정의
    field_map = {
        "T1H": lambda value: f" - Temperature: {value}°C",
        "RN1": lambda value: f" - 1-hour Precipitation: {value} mm",
        "SKY": lambda value: f" - Sky Condition: {sky_map.get(value, 'Unknown')}",
        "UUU": lambda value: f" - East-West Wind Component: {value} m/s",
        "VVV": lambda value: f" - North-South Wind Component: {value} m/s",
        "REH": lambda value: f" - Humidity: {value}%",
        "PTY": lambda value: f" - Precipitation Type: {pty_map.get(value, 'Unknown')}",
        "LGT": lambda value: f" - Lightning: {value} kA",
        "VEC": lambda value: f" - Wind Direction: {value} degrees",
        "WSD": lambda value: f" - Wind Speed: {value} m/s"
    }
    for time, data in weather_data.items():
        temp = []
        # 각 필드에 대해 정의된 처리 함수를 적용
        for field, process in field_map.items():
            if field in data:
                temp.append(process(data[field]))
        facts[time] = temp
    return facts

# gpt의 프롬프트 결과를 반환하는 함수
def weatherman(facts: List[str], tone: str, length_words: int, style: str, date_time : str):
    prompt_role = "You are a weatherman. \
    Your task is to brief through data from the FACTS. \
    FACTS is weather data within the near time from the current time. \
    You should respect the instructions: the TONE, the LENGTH, the DATE_TIME, and the STYLE"
    facts_list = []
    for time, details in facts.items():
        facts_list.append(f"{', '.join(details)}")
    facts_str = ", ".join(facts_list)
    prompt = f"{prompt_role} \
    FACTS: {facts_str} \
    TONE: {tone} \
    LENGTH: {length_words} words \
    STYLE: {style} \
    DATE_TIME: {date_time}"
    response = ask_chatgpt([{"role": "user", "content": prompt}])
    sentences = re.split(r'(?<=[.!?])\s+', response)
    return '\n'.join(sentences)

# 날씨서비스의 GET요청 인자 base_time 계산
def get_base_datetime():
    now = datetime.now()
    if now.minute < 45: # 45분 이전
        now -= timedelta(hours=1)
        base_time = now.replace(minute=30).strftime('%H%M')
    else: # 45분 이후
        base_time = now.replace(minute=30).strftime('%H%M')
    base_date = now.strftime('%Y%m%d')
    return base_date, base_time

def index(request):
    base_date, base_time = get_base_datetime()
    date_time_str = f"{base_date} {base_time}"

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            lat,lon = convert_to_xy(float(longitude),float(latitude))
            location = f"{lat},{lon}"

            if not Weather.objects.filter(date_time=date_time_str, location=location).exists():
                # Celery 작업 추가
                task = task_add.delay(latitude, longitude, base_date, base_time)
                # 작업 ID를 반환하여 클라이언트에서 이후 작업을 계속하도록 유도
                return JsonResponse({'task_id': task.id}, status=200)

            latest_weather = Weather.objects.filter(
                date_time=date_time_str, location=location).latest('recorded')
            facts = parse_weather_data(latest_weather.data)
            res = weatherman(facts, "informal", 100, "news flash", str(timezone.now()))
            context = {
                'gpt_weather': res,
                'original_weather': json.dumps(facts),
                'current_time': str(timezone.now())
            }
            return render(request, 'app/weather_cast.html', context)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data'}, status=400)

    elif request.method == 'GET':
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        location = ""
        if latitude and longitude:
            lat,lon = convert_to_xy(float(longitude),float(latitude))
            location = f"{lat},{lon}"

        if location and Weather.objects.filter(date_time=date_time_str, location=location).exists():
            latest_weather = Weather.objects.filter(
                date_time=date_time_str, location=location).latest('recorded')
            facts = parse_weather_data(latest_weather.data)
            res = weatherman(facts, "informal", 100, "news flash", str(timezone.now()))
            context = {
                'gpt_weather': res,
                'original_weather': json.dumps(facts),
                'current_time': str(timezone.now())
            }
            return render(request, 'app/weather_cast.html', context)
        else:
            return render(request, 'app/loading.html', {})
    return render(request,'app/loading.html',{})


def task_status(request, task_id):
    try:
        result = AsyncResult(task_id, app=app)  # Celery 앱 객체를 사용
        status = result.status
        logger.debug(f"Task status for {task_id}: {status}")
        
        if status == 'SUCCESS':
            return JsonResponse({'status': 'SUCCESS', 'result': result.result})
        elif status == 'FAILURE':
            return JsonResponse({'status': 'FAILURE', 'result': str(result.result)})
        else:
            return JsonResponse({'status': 'PENDING'})
    except Exception as e:
        logger.error(f"Error fetching task status for {task_id}: {e}")
        return JsonResponse({'status': 'ERROR', 'message': str(e)}, status=500)

def page_not_found(request, exception):
    return render(request, 'app/404.html', {})

def save_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            # 위치 정보를 처리하거나 저장하는 로직을 추가합니다.
            # Celery 작업 추가
            task = task_add.delay(latitude, longitude)
            return JsonResponse({'status': 'success', 'task_id': task.id}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid data'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
