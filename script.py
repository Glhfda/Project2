from flask import Flask, request, render_template, redirect, url_for, flash, session
import requests
from dotenv import load_dotenv
import os
import logging
import json
from dash import Dash, dcc, html
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)se%(levelname)s %(name)s %(threadName)s : %(message)s',
    filename='app.log',
    filemode='a'
)

API_KEY = os.getenv('API_KEY')

def check_bad_weather(temperature, wind, precip_prob):
    try:
        if temperature > 35:
            if wind > 20:
                if precip_prob > 70:
                    return ('Очень жаркая погода с сильным ветром и высокой вероятностью осадков. '
                            'Избегайте длительного пребывания на улице.')
                else:
                    return ('Очень жаркая погода с сильным ветром. '
                            'Запаситесь водой и избегайте прямых солнечных лучей.')
            elif precip_prob > 70:
                return ('Очень жаркая погода с высокой вероятностью осадков. '
                        'Избегайте длительного пребывания на улице.')
            else:
                return ('Очень жаркая и сухая погода. '
                        'Пейте много воды и избегайте физической нагрузки в полдень.')
        elif temperature > 25:
            if wind > 20:
                if precip_prob > 70:
                    return ('Тёплая погода с сильным ветром и осадками. '
                            'Возьмите зонтик и ветровку.')
                else:
                    return ('Тёплая погода с сильным ветром. '
                            'Возьмите ветровку.')
            elif precip_prob > 70:
                return ('Тёплая погода с осадками. '
                        'Возьмите зонтик.')
            else:
                return ('Тёплая погода без сильного ветра и высокой вероятности осадков. '
                        'Подходит для прогулок.')
        elif temperature > 15:
            if wind > 20:
                if precip_prob > 70:
                    return ('Прохладно, ветрено и осадки. '
                            'Возьмите защиту от дождя.')
                else:
                    return ('Прохладно и ветрено. '
                            'Учтите ветер при планировании.')
            elif precip_prob > 70:
                return ('Прохладно и есть осадки. '
                        'Возьмите зонтик.')
            else:
                return ('Прохладная и спокойная погода. '
                        'Подходит для прогулок.')
        elif temperature > 0:
            if wind > 20:
                if precip_prob > 70:
                    return ('Холодно, ветрено и осадки. '
                            'Нужна тёплая одежда и зонтик.')
                else:
                    return ('Холодно и небольшой ветер. '
                            'Нужна тёплая одежда.')
            elif precip_prob > 70:
                return ('Холодно и осадки. '
                        'Тёплая одежда и зонтик обязательны.')
            else:
                return ('Холодно и сухо. '
                        'Нужна тёплая одежда.')
        else:
            if wind > 20:
                if precip_prob > 70:
                    return ('Морозно, сильный ветер и осадки. '
                            'Очень тёплая одежда необходима.')
                else:
                    return ('Морозно и ветрено. '
                            'Очень тёплая одежда необходима.')
            elif precip_prob > 70:
                return ('Морозно и осадки. '
                        'Тёплая одежда обязательна.')
            else:
                return ('Морозно и сухо. '
                        'Тёплая одежда обязательна.')
    except Exception as e:
        logging.error(f"Ошибка check_bad_weather: {e}")
        return "Не удалось оценить погодные условия."

def get_location_data(city_name, api_key):
    url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
    params = {
        'apikey': api_key,
        'q': city_name,
        'language': 'ru-RU'
    }
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data and 'GeoPosition' in data[0]:
        location = data[0]
        location_key = location['Key']
        lat = location['GeoPosition']['Latitude']
        lon = location['GeoPosition']['Longitude']
        return {'key': location_key, 'lat': lat, 'lon': lon}
    else:
        logging.warning(f"Город '{city_name}' не найден или нет координат.")
        return None

def get_current_weather(location_key, api_key):
    url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}'
    params = {
        'apikey': api_key,
        'details': 'true',
        'language': 'ru-RU'
    }
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()

def get_hourly_forecast(location_key, api_key):
    url = f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{location_key}'
    params = {
        'apikey': api_key,
        'metric': 'true',
        'language': 'ru-RU'
    }
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()

def extract_current_weather(data):
    current_weather = data[0]
    temperature = current_weather['Temperature']['Metric']['Value']
    wind_speed = current_weather['Wind']['Speed']['Metric']['Value']
    return temperature, wind_speed

def extract_precipitation_probability(forecast_data):
    current_hour_forecast = forecast_data[0]
    precip_prob = current_hour_forecast.get('PrecipitationProbability', 0)
    return precip_prob

def get_daily_forecast(location_key, api_key, days=1):
    url = f'http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{location_key}'
    params = {
        'apikey': api_key,
        'metric': 'true',
        'language': 'ru-RU',
        'details': 'true'
    }
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    return response.json()

def process_forecast_data(data):
    forecasts = data.get('DailyForecasts', [])
    result = []
    for day in forecasts:
        date_raw = day.get('Date', '')
        try:
            date_obj = datetime.fromisoformat(date_raw)
            date_str = date_obj.strftime('%Y-%m-%d %H:%M')
        except Exception:
            date_str = date_raw

        min_temp = day['Temperature']['Minimum']['Value']
        max_temp = day['Temperature']['Maximum']['Value']
        wind_speed = day['Day']['Wind']['Speed']['Value']
        precipitation_probability = day['Day']['PrecipitationProbability']
        weather_text_day = day['Day']['IconPhrase']
        weather_text_night = day['Night']['IconPhrase']

        result.append({
            'date': date_str,
            'min_temp': min_temp,
            'max_temp': max_temp,
            'wind_speed': wind_speed,
            'precip_prob': precipitation_probability,
            'weather_text_day': weather_text_day,
            'weather_text_night': weather_text_night
        })
    return result

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_weather', methods=['POST'])
def check_weather_route():
    start_city = request.form.get('start')
    end_city = request.form.get('end')
    stops_line = request.form.get('stops_line', '')
    stops = [s.strip() for s in stops_line.split() if s.strip()]
    days = int(request.form.get('days', 1))

    if not start_city or not end_city:
        flash('Пожалуйста, заполните начальную и конечную точки.')
        return redirect(url_for('home'))

    route_points = [start_city] + stops + [end_city]

    points_data = []
    for city in route_points:
        loc_data = get_location_data(city, API_KEY)
        if not loc_data:
            flash(f"Не удалось найти точку: {city}. Попробуйте другой город.")
            return redirect(url_for('home'))
        points_data.append({
            'city': city,
            'key': loc_data['key'],
            'lat': loc_data['lat'],
            'lon': loc_data['lon']
        })

    if days > 1 or stops:
        forecasts_by_points = []
        for p in points_data:
            daily_data = get_daily_forecast(p['key'], API_KEY, days=days)
            processed_data = process_forecast_data(daily_data)
            forecasts_by_points.append({
                'city': p['city'],
                'forecast': processed_data,
                'lat': p['lat'],
                'lon': p['lon']
            })
        session['forecasts_data'] = json.dumps(forecasts_by_points)
        session['days'] = days
        session['is_new_forecast'] = True

        return render_template('result.html',
                               start_city=start_city,
                               temperature_start=None,
                               wind_speed_start=None,
                               precip_prob_start=None,
                               weather_status_start=None,
                               end_city=end_city,
                               temperature_end=None,
                               wind_speed_end=None,
                               precip_prob_end=None,
                               weather_status_end=None,
                               forecasts=forecasts_by_points,
                               days=days,
                               is_new_forecast=True)
    else:
        # Одиночный прогноз для начальной и конечной точки (без промежуточных)
        start_key = points_data[0]['key']
        end_key = points_data[-1]['key']

        current_weather_start = get_current_weather(start_key, API_KEY)
        temperature_start, wind_speed_start = extract_current_weather(current_weather_start)
        hourly_forecast_start = get_hourly_forecast(start_key, API_KEY)
        precip_prob_start = extract_precipitation_probability(hourly_forecast_start)
        weather_status_start = check_bad_weather(temperature_start, wind_speed_start, precip_prob_start)

        current_weather_end = get_current_weather(end_key, API_KEY)
        temperature_end, wind_speed_end = extract_current_weather(current_weather_end)
        hourly_forecast_end = get_hourly_forecast(end_key, API_KEY)
        precip_prob_end = extract_precipitation_probability(hourly_forecast_end)
        weather_status_end = check_bad_weather(temperature_end, wind_speed_end, precip_prob_end)

        forecasts_single_day = []
        forecasts_single_day.append({
            'city': start_city,
            'forecast': [],
            'lat': points_data[0]['lat'],
            'lon': points_data[0]['lon']
        })
        forecasts_single_day.append({
            'city': end_city,
            'forecast': [],
            'lat': points_data[-1]['lat'],
            'lon': points_data[-1]['lon']
        })

        session['forecasts_data'] = json.dumps(forecasts_single_day)
        session['days'] = 1
        session['is_new_forecast'] = False

        return render_template('result.html',
                               start_city=start_city,
                               temperature_start=temperature_start,
                               wind_speed_start=wind_speed_start,
                               precip_prob_start=precip_prob_start,
                               weather_status_start=weather_status_start,
                               end_city=end_city,
                               temperature_end=temperature_end,
                               wind_speed_end=wind_speed_end,
                               precip_prob_end=precip_prob_end,
                               weather_status_end=weather_status_end,
                               forecasts=forecasts_single_day,
                               days=1,
                               is_new_forecast=False)

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Непредвиденная ошибка: {e}")
    flash("Произошла непредвиденная ошибка. Попробуйте позже.")
    return redirect(url_for('home'))

dash_app = Dash(__name__, server=app, url_base_pathname='/dash_app/')
dash_app.title = "Интерактивная визуализация погоды"

dash_app.layout = html.Div(children=[
    html.H1("Интерактивная визуализация прогноза погоды"),
    html.P("Выберите параметр для отображения:"),
    dcc.Dropdown(
        id='parameter-dropdown',
        options=[
            {'label': 'Макс. Температура', 'value': 'max_temp'},
            {'label': 'Мин. Температура', 'value': 'min_temp'},
            {'label': 'Скорость ветра', 'value': 'wind_speed'},
            {'label': 'Вероятность осадков', 'value': 'precip_prob'}
        ],
        value='max_temp'
    ),
    dcc.Graph(id='weather-graph'),
    html.A("Назад", href='/', style={'display':'block','margin-top':'20px'})
])

@dash_app.callback(
    Output('weather-graph', 'figure'),
    Input('parameter-dropdown', 'value')
)
def update_graph(selected_parameter):
    forecasts_data = json.loads(session.get('forecasts_data', '[]'))
    if not forecasts_data or len(forecasts_data) == 0:
        return go.Figure()

    fig = go.Figure()
    has_data = any(len(x['forecast']) > 0 for x in forecasts_data)

    if has_data:
        for point in forecasts_data:
            city = point['city']
            if len(point['forecast']) > 0:
                x = [f['date'] for f in point['forecast']]
                y = [f[selected_parameter] for f in point['forecast']]
                fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=city))
        fig.update_layout(
            title="Прогноз погоды по маршруту",
            xaxis_title="Дата",
            yaxis_title=selected_parameter,
            legend_title="Город"
        )
    else:
        fig.update_layout(title="Нет данных для графика")

    return fig

if __name__ == "__main__":
    app.run(debug=True)
