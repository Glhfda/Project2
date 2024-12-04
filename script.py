from flask import Flask, request, render_template, redirect, url_for, flash
import requests
from dotenv import load_dotenv
import os
import logging

# Загрузка переменных окружения из .env файла
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)se%(levelname)s %(name)s %(threadName)s : %(message)s',
                    filename='app.log',
                    filemode='a')

API_KEY = os.getenv('API_KEY')

def check_bad_weather(temperature, wind, precip_prob):
    try:
        if temperature > 35:
            if wind > 20:
                if precip_prob > 70:
                    return ('Очень жаркая погода с сильным ветром и высокой вероятностью осадков. '
                            'Необходимо избегать длительного пребывания на улице.')
                else:
                    return ('Очень жаркая погода с сильным ветром. '
                            'Стоит запастись водой и избегать попадания прямых солнечных лучей.')
            elif precip_prob > 70:
                return ('Очень жаркая погода с высокой вероятностью осадков. '
                        'Необходимо избегать длительного пребывания на улице.')
            else:
                return ('Очень жаркая и сухая погода. '
                        'Необходимо пить много воды и избегать физической нагрузки в полуденные часы.')

        elif temperature > 25:
            if wind > 20:
                if precip_prob > 70:
                    return ('Тёплая погода с сильным ветром и высокой вероятностью осадков. '
                            'Рекомендуется взять зонтик и защиту от ветра.')
                else:
                    return ('Тёплая погода с сильным ветром. '
                            'Стоит продумать защиту от ветра, например, надеть ветровку.')
            elif precip_prob > 70:
                return ('Тёплая погода с высокой вероятностью осадков. '
                        'Рекомендуется взять зонтик и следить за прогнозом.')
            else:
                return ('Тёплая и хорошая погода без сильного ветра и высокой вероятности осадков. '
                        'Можно легко одеваться и планировать мероприятия на открытом воздухе.')

        elif temperature > 15:
            if wind > 20:
                if precip_prob > 70:
                    return ('Прохладная погода с ветром и высокой вероятностью осадков. '
                            'Рекомендуется взять защиту от дождя и обратить внимание на скорость ветра.')
                else:
                    return ('Прохладная погода с ветром. '
                            'Стоит учитывать скорость ветра при планировании активностей.')
            elif precip_prob > 70:
                return ('Прохладная погода с высокой вероятностью осадков. '
                        'Рекомендуется взять зонтик или плащ.')
            else:
                return ('Прохладная и спокойная погода. '
                        'Подходит для прогулок.')

        elif temperature > 0:
            if wind > 20:
                if precip_prob > 70:
                    return ('Холодная погода с ветром и высокой вероятностью осадков. '
                            'Необходимо утепляться и брать зонтик.')
                else:
                    return ('Холодная погода со слабым ветром. '
                            'Рекомендуется надеть теплую одежду.')
            elif precip_prob > 70:
                return ('Холодная погода с высокой вероятностью осадков. '
                        'Рекомендуется надеть теплую одежду и взять зонтик.')
            else:
                return ('Холодная и сухая погода. '
                        'Необходимо надеть теплую одежду.')

        else:
            if wind > 20:
                if precip_prob > 70:
                    return ('Морозная погода с ветром и высокой вероятностью осадков. '
                            'Рекомендуется носить утепленную одежду.')
                else:
                    return ('Морозная погода с ветром. '
                            'Рекомендуется носить теплую одежду.')
            elif precip_prob > 70:
                return ('Морозная погода с высокой вероятностью осадков. '
                        'Рекомендуется носить теплую одежду.')
            else:
                return ('Морозная и сухая погода. '
                        'Рекомендуется носить теплую одежду.')
    except Exception as e:
        logging.error(f"Ошибка в функции check_bad_weather: {e}")
        return "Не удалось оценить погодные условия."

def get_location_key(city_name, api_key):
    url = 'http://dataservice.accuweather.com/locations/v1/cities/search'
    params = {
        'apikey': api_key,
        'q': city_name,
        'language': 'ru-RU'
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]['Key']
        else:
            logging.warning(f"Город '{city_name}' не найден.")
            return None
    except requests.Timeout:
        logging.error(f"Тайм-аут при запросе location key для города '{city_name}'.")
        return None
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе location key для города '{city_name}': {e}")
        return None

def get_current_weather(location_key, api_key):
    url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}'
    params = {
        'apikey': api_key,
        'details': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logging.error("Тайм-аут при запросе текущей погоды.")
        return None
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе текущей погоды: {e}")
        return None

def get_hourly_forecast(location_key, api_key):
    url = f'http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{location_key}'
    params = {
        'apikey': api_key,
        'metric': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        logging.error("Тайм-аут при запросе почасового прогноза погоды.")
        return None
    except requests.RequestException as e:
        logging.error(f"Ошибка при запросе почасового прогноза погоды: {e}")
        return None

def extract_current_weather(data):
    try:
        current_weather = data[0]
        temperature = current_weather['Temperature']['Metric']['Value']
        wind_speed = current_weather['Wind']['Speed']['Metric']['Value']
        return temperature, wind_speed
    except (IndexError, KeyError, TypeError) as e:
        logging.error(f"Ошибка при извлечении текущей погоды: {e}")
        return None, None

def extract_precipitation_probability(forecast_data):
    try:
        if not forecast_data:
            logging.warning("Почасовой прогноз пуст.")
            return 0
        # Предположим, что нас интересует вероятность осадков на текущий час
        current_hour_forecast = forecast_data[0]
        precip_prob = current_hour_forecast.get('PrecipitationProbability', 0)
        return precip_prob
    except (IndexError, KeyError, TypeError) as e:
        logging.error(f"Ошибка при извлечении вероятности осадков: {e}")
        return 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check_weather', methods=['POST'])
def check_weather_route():
    try:
        start_city = request.form.get('start')
        end_city = request.form.get('end')

        # Проверка на заполненность полей
        if not start_city or not end_city:
            flash('Пожалуйста, заполните оба поля: начальную и конечную точки.')
            return redirect(url_for('home'))

        # Получаем location keys для начальной и конечной точек
        start_location_key = get_location_key(start_city, API_KEY)
        if not start_location_key:
            flash(f"Не удалось найти начальную точку: {start_city}. Проверьте название города.")
            return redirect(url_for('home'))

        end_location_key = get_location_key(end_city, API_KEY)
        if not end_location_key:
            flash(f"Не удалось найти конечную точку: {end_city}. Проверьте название города.")
            return redirect(url_for('home'))

        # Получаем погодные данные для начальной точки
        current_weather_start = get_current_weather(start_location_key, API_KEY)
        if not current_weather_start:
            flash("Не удалось получить текущую погоду для начальной точки.")
            return redirect(url_for('home'))

        temperature_start, wind_speed_start = extract_current_weather(current_weather_start)
        if temperature_start is None or wind_speed_start is None:
            flash("Не удалось извлечь температуру или скорость ветра для начальной точки.")
            return redirect(url_for('home'))

        # Получаем почасовой прогноз для вероятности осадков начальной точки
        hourly_forecast_start = get_hourly_forecast(start_location_key, API_KEY)
        if not hourly_forecast_start:
            flash("Не удалось получить почасовой прогноз погоды для начальной точки.")
            return redirect(url_for('home'))

        precip_prob_start = extract_precipitation_probability(hourly_forecast_start)

        # Оценка погодных условий для начальной точки
        weather_status_start = check_bad_weather(temperature_start, wind_speed_start, precip_prob_start)

        # Получаем погодные данные для конечной точки
        current_weather_end = get_current_weather(end_location_key, API_KEY)
        if not current_weather_end:
            flash("Не удалось получить текущую погоду для конечной точки.")
            return redirect(url_for('home'))

        temperature_end, wind_speed_end = extract_current_weather(current_weather_end)
        if temperature_end is None or wind_speed_end is None:
            flash("Не удалось извлечь температуру или скорость ветра для конечной точки.")
            return redirect(url_for('home'))

        # Получаем почасовой прогноз для вероятности осадков конечной точки
        hourly_forecast_end = get_hourly_forecast(end_location_key, API_KEY)
        if not hourly_forecast_end:
            flash("Не удалось получить почасовой прогноз погоды для конечной точки.")
            return redirect(url_for('home'))

        precip_prob_end = extract_precipitation_probability(hourly_forecast_end)

        # Оценка погодных условий для конечной точки
        weather_status_end = check_bad_weather(temperature_end, wind_speed_end, precip_prob_end)

        # Передача данных в шаблон для отображения
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
                               weather_status_end=weather_status_end)

    except requests.Timeout:
        # Обработка тайм-аута при запросах к API
        flash("Время ожидания ответа от сервиса погоды истекло. Пожалуйста, попробуйте позже.")
        logging.error("Тайм-аут при запросе к API AccuWeather.")
        return redirect(url_for('home'))

    except requests.ConnectionError:
        # Обработка ошибок соединения
        flash("Не удалось установить соединение с сервисом погоды. Проверьте ваше интернет-соединение.")
        logging.error("Ошибка соединения при запросе к API AccuWeather.")
        return redirect(url_for('home'))

    except Exception as e:
        # Обработка всех остальных неожиданных ошибок
        flash("Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.")
        logging.error(f"Непредвиденная ошибка в функции check_weather_route: {e}")
        return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)