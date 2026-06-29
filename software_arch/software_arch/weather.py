import requests
import time
from functools import lru_cache

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self._weather_cache = {}  # Cache for weather data
        self._location_cache = {}  # Cache for location info
        self._cache_timeout = 3600  # 1 hour cache timeout
    
    def _get_cache_key(self, lat, lon, precision=4):
        """Generate cache key with reduced precision"""
        return (round(lat, precision), round(lon, precision))
    
    def get_weather_by_coords(self, lat, lon):
        """Get weather data with caching"""
        cache_key = self._get_cache_key(lat, lon)
        current_time = time.time()
        
        # Check cache
        if cache_key in self._weather_cache:
            cached_data, cached_time = self._weather_cache[cache_key]
            if current_time - cached_time < self._cache_timeout:
                return cached_data
        
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.api_key}&units=metric"
            r = requests.get(url, timeout=5).json()

            weather_data = {
                'humidity': r['main']['humidity'],
                'rainfall': r.get('rain', {}).get('1h', 0.0),
                'wind': r['wind']['speed'],
                'pressure': r['main']['pressure'],
                'temp': r['main']['temp']
            }
            
            # Cache the result
            self._weather_cache[cache_key] = (weather_data, current_time)
            return weather_data
        except Exception as e:
            # Return cached data if available even if expired
            if cache_key in self._weather_cache:
                return self._weather_cache[cache_key][0]
            # Return default values on error
            return {
                'humidity': 0,
                'rainfall': 0.0,
                'wind': 0.0,
                'pressure': 1013.25,
                'temp': 20.0
            }

    def get_location_info(self, lat, lon):
        """Get location info with caching"""
        cache_key = self._get_cache_key(lat, lon)
        current_time = time.time()
        
        # Check cache
        if cache_key in self._location_cache:
            cached_location, cached_time = self._location_cache[cache_key]
            if current_time - cached_time < self._cache_timeout * 24:  # 24 hours for location
                return cached_location
        
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=en"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            response.raise_for_status()
            data = response.json()
            address = data.get("address", {})
            city = address.get("city") or address.get("province") or address.get("state", "")
            district = (
                address.get("town") or
                address.get("village") or
                address.get("hamlet") or
                address.get("county") or
                address.get("municipality", "")
            )

            location = f"{district}, {city}" if city or district else "Unknown Location"
            
            # Cache the result
            self._location_cache[cache_key] = (location, current_time)
            return location
        except Exception:
            # Return cached data if available
            if cache_key in self._location_cache:
                return self._location_cache[cache_key][0]
            return "Location Could Not Be Retrieved"