from dataclasses import dataclass
from typing import Optional
import aiohttp
from config import t, LANG_EN, log

@dataclass
class WeatherSummary:
    temp: Optional[float]
    feels_like: Optional[float]
    condition: str
    wind: Optional[float]
    clouds: Optional[int]
    rain_mm: float
    snow_mm: float

def _mm_from(obj: Optional[dict]) -> float:
    if not obj:
        return 0.0
    return float(obj.get("1h") or obj.get("3h") or 0.0)

async def geocode_city(session: aiohttp.ClientSession, api_key: str, city: str):
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    async with session.get(url, params=params, timeout=20) as resp:
        resp.raise_for_status()
        data = await resp.json()
        if not data:
            return None
        top = data[0]
        return {"name": f"{top.get('name')}, {top.get('country')}", "lat": top["lat"], "lon": top["lon"]}

async def fetch_current_weather(session: aiohttp.ClientSession, api_key: str, lat: float, lon: float) -> Optional[WeatherSummary]:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "lang": "en"}
    async with session.get(url, params=params, timeout=20) as resp:
        if resp.status != 200:
            log.warning("OWM current weather failed: %s", await resp.text())
            return None
        j = await resp.json()

    condition = (j.get("weather") or [{}])[0].get("description", "weather unavailable")
    main = j.get("main") or {}
    wind = j.get("wind") or {}
    clouds = j.get("clouds") or {}
    return WeatherSummary(
        temp=main.get("temp"),
        feels_like=main.get("feels_like"),
        condition=condition,
        wind=wind.get("speed"),
        clouds=clouds.get("all"),
        rain_mm=_mm_from(j.get("rain")),
        snow_mm=_mm_from(j.get("snow")),
    )

def make_advice(w: WeatherSummary, lang: str) -> str:
    tips = []
    c = (w.condition or "").lower()
    if w.rain_mm > 0 or "rain" in c or "drizzle" in c or "shower" in c:
        tips.append(t(lang, "advice_umbrella"))
    if w.snow_mm > 0 or "snow" in c:
        tips.append(t(lang, "advice_snow_shoes"))

    if w.temp is not None:
        temp = float(w.temp)
        if temp <= 3: tips.append(t(lang, "advice_very_cold"))
        elif temp <= 7: tips.append(t(lang, "advice_warm_coat"))
        elif temp <= 14: tips.append(t(lang, "advice_light_jacket"))
        elif temp <= 22: tips.append(t(lang, "advice_comfy"))
        elif temp <= 27: tips.append(t(lang, "advice_warm"))
        else: tips.append(t(lang, "advice_hot"))

    if w.wind is not None:
        try:
            wind = float(w.wind)
            if wind >= 13: tips.append(t(lang, "advice_very_windy"))
            elif wind >= 8: tips.append(t(lang, "advice_breezy"))
        except (TypeError, ValueError):
            pass

    if (w.clouds is not None) and (w.rain_mm == 0) and ("rain" not in c):
        if w.clouds >= 80: tips.append(t(lang, "advice_overcast"))
        elif w.clouds >= 60: tips.append(t(lang, "advice_mostly_cloudy"))

    if not tips:
        return t(lang, "advice_default")
    dedup = []
    for tip in tips:
        if tip not in dedup:
            dedup.append(tip)
    return " • ".join(dedup[:3])

def format_weather_list(w: WeatherSummary, lang: str) -> str:
    parts = []
    if w.temp is not None and w.feels_like is not None:
        parts.append(t(lang, "w_temp", t=round(w.temp), fl=round(w.feels_like)))
    elif w.temp is not None:
        parts.append(t(lang, "w_temp_simple", t=round(w.temp)))
    parts.append(t(lang, "w_condition", cond=w.condition))
    if w.wind is not None:
        parts.append(t(lang, "w_wind", w=w.wind))
    if w.clouds is not None:
        parts.append(t(lang, "w_clouds", c=w.clouds))
    if w.rain_mm > 0:
        parts.append(t(lang, "w_rain", mm=w.rain_mm))
    if w.snow_mm > 0:
        parts.append(t(lang, "w_snow", mm=w.snow_mm))
    return "\n".join(parts)
