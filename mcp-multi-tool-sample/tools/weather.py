import asyncio

async def get_weather_async(city: str):
    # Mocked weather data for offline demo
    return {
        "city": city,
        "temp_c": 28.3,
        "humidity_pct": 62,
        "summary": "Partly cloudy (mock)",
        "note": "Replace with a real API if you prefer."
    }

def get_weather_sync(city: str):
    return asyncio.get_event_loop().run_until_complete(get_weather_async(city))
