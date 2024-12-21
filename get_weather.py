import requests

weather_key = 'OTXUjD8GqHevHoR8A2zL6Dtx8id92VRe'
maps_key = 'f4f93036-6275-4cab-ae33-702e1ce115e3'


def location_key(lat: float, lon: float):
    '''Получает ключ локации по координатам'''
    try:
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("Неккоректные значения широты и долготы")
        api_url = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search'
        response = requests.get(api_url, params={"apikey": weather_key,
                                                 "q": f"{lat},{lon}",
                                                 "language": "ru",
                                                 "details": "true"})
        response.raise_for_status()
        data = response.json()
        if "Key" not in data:
            raise ValueError("Ключ локации не найден, проверьте корректность координат")
        return data['Key']
    except ValueError as e:
        raise ValueError(e)
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(e)


def get_weather_by_coords(lat: float, lon: float, days):
    '''Возвращает информацию о погоде по координатам'''
    try:
        loc_key = location_key(lat, lon)
        response = requests.get(f"http://dataservice.accuweather.com/forecasts/v1/daily/{days}day/{loc_key}",
                                params={"apikey": weather_key,
                                        "language": "ru",
                                        "details": "true",
                                        "metric": "true"})
        response.raise_for_status()
        data = response.json()
        temperature = [round((data['DailyForecasts'][day]['Temperature']['Minimum']['Value'] +
                              data['DailyForecasts'][day]['Temperature']['Maximum']['Value']) / 2, 2) for day in
                       range(days)]
        humidity = [round((data['DailyForecasts'][day]['Day']['RelativeHumidity']['Average'] +
                           data['DailyForecasts'][day]['Night']['RelativeHumidity']['Average']) / 2, 2) for day in
                    range(days)]
        wind_speed = [round((data['DailyForecasts'][day]['Day']['Wind']['Speed']['Value'] +
                             data['DailyForecasts'][day]['Night']['Wind']['Speed']['Value']) / 2, 2) for day in
                      range(days)]
        rain_probability = [round((data['DailyForecasts'][day]['Day']['RainProbability'] +
                                   data['DailyForecasts'][day]['Night']['RainProbability']) / 2, 2) for day in
                            range(days)]
        return {"temperature": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "rain_probability": rain_probability
                }

    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(f"Произошла ошибка HTTP: {e}")
    except Exception as e:
        raise Exception(e)


def send_maps_request(data: str):
    '''Отправляет запрос в Яндекс.Карты'''
    api_url = 'https://geocode-maps.yandex.ru/1.x/'
    r = requests.get(api_url,
                     params=dict(format='json',
                                 apikey=maps_key,
                                 geocode=data))
    if r.status_code == 200:
        return r.json()['response']
    elif r.status_code == 403:
        raise Exception('Такого адреса|координат нет.')
    else:
        raise Exception('Что-то пошло не так.')


def get_coords_by_address(address: str):
    '''Получает координаты по названию города'''
    coords = send_maps_request(address)['GeoObjectCollection']['featureMember']

    if not coords:
        raise Exception(f'Координаты города {address} отсуствуют.')

    coords = coords[0]['GeoObject']['Point']['pos']
    lon, lat = coords.split(' ')
    return float(lat), float(lon)
