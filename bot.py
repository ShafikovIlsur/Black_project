import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from get_weather import get_weather_by_coords, get_coords_by_address

API_TOKEN = '7883612363:AAF40N-mjwtMiG7nN0OUacSuBXpu9g3qLZM'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Логирование
logging.basicConfig(level=logging.INFO)


# Определяем состояния для FSM
class WeatherStates(StatesGroup):
    start_city = State()
    end_city = State()
    start_coordinates = State()
    end_coordinates = State()
    forecast_interval = State()


# Команда /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот прогноза погоды. Используйте команду /weather для прогноза."
    )


# Команда /help
@dp.message(Command("help"))
async def help(message: types.Message):
    await message.answer("Доступные команды: /start, /help, /weather")


# Команда /weather для запуска алгоритма
@dp.message(Command("weather"))
async def weather(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название начального города"
    )
    await state.set_state(WeatherStates.start_city)


# Обработка начальных координат
@dp.message(WeatherStates.start_city)
async def get_start_coordinates(message: types.Message, state: FSMContext):
    try:
        start_lat, start_lon = get_coords_by_address(message.text)
        await state.update_data(start_coordinates=(start_lat, start_lon), start_city=message.text)
        await message.answer(
            "Введите конечный город"
        )
        await state.set_state(WeatherStates.end_city)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# Обработка конечных координат
@dp.message(WeatherStates.end_city)
async def get_end_coordinates(message: types.Message, state: FSMContext):
    try:
        end_lat, end_lon = get_coords_by_address(message.text)
        await state.update_data(end_coordinates=(end_lat, end_lon), end_city=message.text)

        # Показать опции временного интервала прогноза
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Прогноз на 1 день", callback_data="forecast_1"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Прогноз на 5 дней", callback_data="forecast_5"
                    )
                ],
            ]
        )
        await message.answer(
            "Выберите временной интервал прогноза:", reply_markup=keyboard
        )
        await state.set_state(WeatherStates.forecast_interval)
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.callback_query(WeatherStates.forecast_interval)
async def send_forecast(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    start_lat, start_lon = data["start_coordinates"]
    end_lat, end_lon = data["end_coordinates"]
    interval = callback_query.data.split("_")[1]

    coordinates = [(start_lat, start_lon), (end_lat, end_lon)]
    weather_data = []
    for lat, lon in coordinates:
        weather_info = get_weather_by_coords(lat, lon, int(interval))

        temperature = ''.join([f'\nДень {day + 1}: {value} °C' for day, value in enumerate(weather_info['temperature'])])
        humidity = ''.join([f'\nДень {day + 1}: {value}%' for day, value in enumerate(weather_info['humidity'])])
        wind_speed = ''.join([f'\nДень {day + 1}: {value} км/ч' for day, value in enumerate(weather_info['wind_speed'])])
        rain_probability = ''.join(
            [f'\nДень {day + 1}: {value}%' for day, value in enumerate(weather_info['rain_probability'])])

        weather_data.append(
            {
                "temperature": temperature,
                'humidity': humidity,
                "wind_speed": wind_speed,
                "rain_probability": rain_probability,
            }
        )
    logging.info(f"{weather_data}")
    forecast = (
        f"Прогноз погоды для маршрута ({data['start_city']}) -> ({data['end_city']})\n\n"
        f"Начальная точка:\n"
        f"Температура: {weather_data[0]['temperature']}\n\n"
        f"Влажность воздуха:{weather_data[0]['humidity']}\n\n"
        f"Скорость ветра: {weather_data[0]['wind_speed']}\n\n"
        f"Вероятность дождя: {weather_data[0]['rain_probability']}\n\n"
        f"Конечная точка:\n"
        f"Температура: {weather_data[1]['temperature']}\n\n"
        f"Влажность воздуха:{weather_data[1]['humidity']}\n\n"
        f"Скорость ветра: {weather_data[1]['wind_speed']}\n\n"
        f"Вероятность дождя: {weather_data[1]['rain_probability']}"
    )

    await bot.send_message(callback_query.from_user.id, forecast)
    await callback_query.answer()

    # Завершить FSM
    await state.clear()


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
