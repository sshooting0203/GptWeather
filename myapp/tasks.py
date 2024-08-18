# app/tasks.py
from config.celery import app
from .models import Weather
from datetime import datetime, timedelta
import json,requests
from django.db import IntegrityError
from django.utils import timezone
import math
from decouple import config
GOOGLE_API_KEY=config('GOOGLE_API')
WEATHER_API_KEY=config('WEATHER_API')

###############begin:가상청 날씨 서비스 좌표로 변환하는 부분#####################
class LamcParameter:
    def __init__(self, Re, grid, slat1, slat2, olon, olat, xo, yo, first):
        self.Re = Re
        self.grid = grid
        self.slat1 = slat1
        self.slat2 = slat2
        self.olon = olon
        self.olat = olat
        self.xo = xo
        self.yo = yo
        self.first = first

def lamcproj(lon, lat, map, code):
    PI = math.asin(1.0) * 2.0
    DEGRAD = PI / 180.0
    RADDEG = 180.0 / PI
    
    re = map.Re / map.grid
    slat1 = map.slat1 * DEGRAD
    slat2 = map.slat2 * DEGRAD
    olon = map.olon * DEGRAD
    olat = map.olat * DEGRAD

    sn = math.tan(PI * 0.25 + slat2 * 0.5) / math.tan(PI * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(PI * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(PI * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    if code == 0:
        ra = math.tan(PI * 0.25 + lat * DEGRAD * 0.5)
        ra = re * sf / math.pow(ra, sn)
        theta = lon * DEGRAD - olon
        if theta > PI:
            theta -= 2.0 * PI
        if theta < -PI:
            theta += 2.0 * PI
        theta *= sn
        x = (ra * math.sin(theta)) + map.xo
        y = (ro - ra * math.cos(theta)) + map.yo
    else:
        xn = x - map.xo
        yn = ro - y + map.yo
        ra = math.sqrt(xn * xn + yn * yn)
        if sn < 0.0:
            ra = -ra
        alat = math.pow((re * sf / ra), (1.0 / sn))
        alat = 2.0 * math.atan(alat) - PI * 0.5
        if abs(xn) <= 0.0:
            theta = 0.0
        else:
            if abs(yn) <= 0.0:
                theta = PI * 0.5
                if xn < 0.0:
                    theta = -theta
            else:
                theta = math.atan2(xn, yn)
        alon = theta / sn + olon
        lat = alat * RADDEG
        lon = alon * RADDEG
    return x, y

###############end:가상청 날씨 서비스 좌표로 변환하는 부분#####################

# 현위치 위,경도 계산(Google Geolocation API사용)

def get_location():
    try:
        url = f'https://www.googleapis.com/geolocation/v1/geolocate?key={GOOGLE_API_KEY}'
        data = {
            'considerIp': True, # 현 IP로 데이터 추출
        }
        result = requests.post(url, data) # 해당 API에 요청을 보내며 데이터를 추출한다.
        result.raise_for_status() # HTTP 오류 발생 시 예외 발생
        result_json = result.json()
        lat = result_json["location"]["lat"] # 현재 위치의 위도 추출
        lng = result_json["location"]["lng"] # 현재 위치의 경도 추출   
        return lat, lng
    except requests.exceptions.RequestException as e: 
        print(f"Network error: {e}") # 네크워크 요청 실패
        return None, None 
    except json.JSONDecodeError as e: 
        print(f"JSON decode error: {e}") # JSON decode 실패
        return None, None 
    except KeyError as e:
        print(f"Key error: {e}") # data[loc]에서 키가 존재하지 않는 경우(KeyError)
        return None, None
    except Exception as e:
        print(f"Index error: {e}")  # 예상치 못한 오류
        return None, None

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

# 날씨서비스의 GET요청 인자 X,Y 계산
def convert_to_xy(lon, lat):
    map = LamcParameter(
        Re=6371.00877,
        grid=5.0,
        slat1=30.0,
        slat2=60.0,
        olon=126.0,
        olat=38.0,
        xo=210 / 5.0,
        yo=675 / 5.0,
        first=0
    )
    x, y = lamcproj(lon, lat, map, 0)
    return int(x + 1.5), int(y + 1.5)

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
##############################################################################
# celery 함수
@app.task()
def task_add(lat,lon):
    base_date, base_time = get_base_datetime()

    # lat, lon = get_location()
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

