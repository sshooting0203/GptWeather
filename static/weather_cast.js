let chart = null;
let lastClickedBar = null; 
document.addEventListener('DOMContentLoaded', function() {
    // JSON 데이터를 콘솔에 출력하여 확인
    const weatherData = document.getElementById('weather-data');
    const parsedWeather = JSON.parse(weatherData.textContent.trim());
    const currentTime = document.getElementById('current-time').textContent.trim();
    const gptWeather = document.getElementById('gpt-weather');

    const table = document.getElementById('weather-table');
    const timeHeaderRow = table.querySelector('#time-header-row');
    const weatherSummaryRow = table.querySelector('#weather-summary-row');

    const {times, temperatures} = createWeatherTable(parsedWeather, timeHeaderRow, weatherSummaryRow);
    const canvas = document.getElementById('temperature-chart');

    const temperatureBar = document.querySelector('#temperature');
    temperatureBar.style.boxShadow = 'inset 0 0 10px 5px rgba(0, 0, 0, 0.5)';
    lastClickedBar = temperatureBar; // 마지막 클릭된 바 항목 업데이트
    typeEffect(gptWeather); // 타이핑 효과 적용
    setBackgroundColor(currentTime); // 배경화면 색상 설정
    drawTemperatureChart(canvas, times, temperatures); // 차트 초기화

    document.querySelectorAll('.bar-part').forEach(bar => { // 클릭 이벤트 리스너 설정
        bar.addEventListener('click', function() {
            const dataType = this.getAttribute('data-type');
            updateChart(parsedWeather, dataType, canvas);
            if (lastClickedBar) {
                lastClickedBar.style.boxShadow = 'none';
            }
            this.style.boxShadow = 'inset 0 0 10px 5px rgba(0, 0, 0, 0.5)';
            lastClickedBar = this; // 마지막 클릭된 바 항목 업데이트
        });
    });
    window.addEventListener('resize', () => {
        if (chart) {
            chart.resize(); // 차트를 자동으로 리사이즈
        }
    });
});
/*배경화면색상 설정하는 함수*/
function setBackgroundColor(currentTime) {
    const hour = new Date(currentTime).getHours();
    const backgroundElement = document.querySelector('.back-ground');
    const { hue, lightness } = getHueAndLightness(hour); // 명도(Lightness) 값을 시간에 비례하여 조절
    
    const color = `hsl(${hue}, 80%, ${lightness}%)`; // HSL 색상 모델을 사용하여 배경색 설정
    backgroundElement.style.backgroundColor = color;
    backgroundElement.style.opacity = '0.7';
    document.querySelectorAll('.txt').forEach(element => {  
        if (lightness > 50) {
            element.style.color = 'black'; // 명도가 50%를 초과하면 텍스트를 흰색으로 변경
        } else {
            element.style.color = 'white'; // 명도가 50% 이하일 때 텍스트를 검정색으로 유지
        }
    });
}

/*시간에 따라 색상 조절 값 반환*/
// (Morning: Light Yellow, Afternoon: Light Blue, Evening: Light Orange, Night: Dark Blue)
function getHueAndLightness(hour) {
    let hue, lightness;
    if (hour >= 6 && hour < 12) {
        hue = 60; 
        lightness = 80 + ((hour - 6) / 6) * 10; // 80%에서 90%까지
    } else if (hour >= 12 && hour < 16) {
        hue = 200; 
        lightness = 70 + ((hour - 12) / 4) * 10; // 70%에서 80%까지
    } else if (hour >= 16 && hour < 19) {
        hue = 30; 
        lightness = 60 + ((hour - 16) / 3) * 10; // 60%에서 70%까지
    } else {
        hue = 240; 
        lightness = 20 + ((hour - 19) / 5) * 10; // 20%에서 30%까지
    }
    return { hue, lightness };
}

/*gpt-prompt 타이핑 효과 함수*/
function typeEffect(gptWeather) {
    const element = gptWeather;
    const text = gptWeather.innerHTML;
    gptWeather.innerHTML = '';
    let index = 0;
    const intervalId = setInterval(() => {
        if (index < text.length) {
            element.textContent += text.charAt(index); // textContent 사용
            index++;
        } else {
            clearInterval(intervalId);
        }
    }, 50);
}

/*날씨 데이터에 따른 날씨 이미지 불러오는 함수*/
function getWeatherImage(weatherInfo) {
    const getCondition = (str) => str.split(':').slice(1).join(':').trim();
    const skyCondition = getCondition(weatherInfo[2]);
    const rn1Condition = getCondition(weatherInfo[6]);
    
    const hour = new Date().getHours();
    const timeOfDay = getTimeOfDay(hour);
    const iconElement = document.getElementById('main-icon');

    ////////////////////////////날씨 이미지 맵 정의//////////////////////////////////
    const weatherImages = {
        day: {
            "Sunny": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/clear-day.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-hail.svg'
            },
            "Partly Cloudy": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/cloudy.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-day-hail.svg'
            },
            "Cloudy": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/cloudy.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/hail.svg'
            }
        },
        night: {
            "Sunny": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/clear-night.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-hail.svg'
            },
            "Partly Cloudy": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night-hail.svg'
            },
            "Cloudy": {
                "None": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/partly-cloudy-night.svg',
                "Rain": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/rain.svg',
                "Rain/Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/sleet.svg',
                "Snow": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/snow.svg',
                "Raindrop": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/drizzle.svg',
                "Raindrop/A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/hail.svg',
                "A snowflake": 'https://bmcdn.nl/assets/weather-icons/v2.0/line/hail.svg'
            }
        }
    };
    /////////////////////////////////////////////////////////////////////////////////////
    const imageUrl = weatherImages[timeOfDay][skyCondition][rn1Condition];
    return imageUrl;
}

/*시간에 따라 낮 또는 밤을 구분*/
function getTimeOfDay(hour) {
    return (hour >= 6 && hour < 18) ? 'day' : 'night';
}

/*.txt의 색상을 가져오는 함수*/
function getTextColor() {
    const txtElement = document.querySelector('.txt');
    const color = window.getComputedStyle(txtElement).color;
    return color;
}

/*날씨 테이블 생성 함수*/
function createWeatherTable(parsedWeather, timeHeaderRow, weatherSummaryRow) {
    const times = [];
    const temperatures = [];

    Object.keys(parsedWeather).forEach(time => {
        const weatherInfo = parsedWeather[time];

        // 시간 데이터를 'HH:MM' 형식으로 변환
        const formattedTime = `${time.slice(0, 2)}:${time.slice(2)}`;
        times.push(formattedTime);

        const temperature = parseFloat(weatherInfo[0].split(':')[1].trim());
        temperatures.push(temperature);

        const th = document.createElement('th');
        th.textContent = formattedTime;
        timeHeaderRow.appendChild(th);

        const tdSummary = document.createElement('td');
        const img = document.createElement('img');
        img.src = getWeatherImage(weatherInfo);
        img.alt = "Weather Icon";
        img.className = "weather-icon";

        tdSummary.appendChild(img);
        weatherSummaryRow.appendChild(tdSummary);
    });

    return { times, temperatures };
}
/*차트 그리기 함수*/
function drawTemperatureChart(canvas, labels, data) {
    if (chart) {
        chart.destroy();
    }
    const textColor = getTextColor();
    const minValue = Math.min(...data) -0.1;
    const maxValue = Math.max(...data) +0.1;
    chart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Temperature (°C)',
                data: data,
                borderColor: textColor, // 선 색상 설정
                backgroundColor: textColor.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: textColor // 범례 텍스트 색상 설정
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '°C';
                            }
                            return label;
                        }
                    },
                    backgroundColor: textColor.replace('rgb', 'rgba').replace(')', ', 0.9)') // 툴팁 배경색 설정
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: textColor // x축 텍스트 색상 설정
                    },
                    grid: {
                        color: textColor.replace('rgb', 'rgba').replace(')', ', 0.2)') // x축 그리드 색상 설정
                    }
                },
                y: {
                    min: minValue, // y축의 최솟값 설정
                    max: maxValue, // y축의 최댓값 설정
                    ticks: {
                        color: textColor // y축 텍스트 색상 설정
                    },
                    grid: {
                        color: textColor.replace('rgb', 'rgba').replace(')', ', 0.2)') // y축 그리드 색상 설정
                    }
                }
            }
        }
    });
    canvas.style.display = 'block'; // 차트 표시
}
/*차트 업데이트 함수*/
function updateChart(weatherData, type, canvas) {
    const {times, data} = extractWeatherData(weatherData, type);
    drawTemperatureChart(canvas, times, data);
}

/*날씨 데이터 추출 함수*/
function extractWeatherData(weatherData, type) {
    // 각 데이터 타입에 대응하는 키워드를 정의합니다.
    const typeMap = {
        "temperature": "Temperature",
        "precipitation": "1-hour Precipitation",
        "skyCondition": "Sky Condition",
        "eastWestWindComponent": "East-West Wind Component",
        "northSouthWindComponent": "North-South Wind Component",
        "humidity": "Humidity",
        "precipitationType": "Precipitation Type",
        "lightning": "Lightning",
        "windDirection": "Wind Direction",
        "windSpeed": "Wind Speed"
    };
    const keyPhrase = typeMap[type];
    const times = [];
    const data = [];

    for (const time in weatherData) {
        if (weatherData.hasOwnProperty(time)) {
            const weatherArray = weatherData[time];
            for (const item of weatherArray) {
                if (item.includes(keyPhrase)) {
                    times.push(time); // 시간을 배열에 추가
                    const match = item.match(/[-\d.]+/g);
                    if (match) {
                        const numberMatch = match.find(value => !isNaN(parseFloat(value)));
                        if (numberMatch) {
                            data.push(parseFloat(numberMatch));
                        }
                    }
                    break; 
                }
            }
        }
    }
    return { times, data };
}