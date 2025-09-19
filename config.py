import os
import logging

# ---------- logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("telegram").setLevel(logging.DEBUG)
logging.getLogger("telegram.ext").setLevel(logging.DEBUG)
log = logging.getLogger("weather-event-bot")

DB_PATH = "bot.db"

# ---------- i18n ----------
LANG_EN = "en"
LANG_RU = "ru"

I18N = {
    "start_pick_lang": {"en": "Hi! Choose your language:", "ru": "Привет! Выберите язык:"},
    "start_help": {
        "en": ("Hi! I remind you about your events and tell you the local weather that day 🌤\n\n"
               "1) Set your city: /setcity Berlin\n"
               "2) Add an event: /addevent Dentist Appointment 20.10.2025\n"
               "3) I’ll message you around 08:00 AM in your city’s timezone.\n\n"
               "Commands: ⚙️\n"
               "• /setcity <city>\n"
               "• /addevent <title> <dd.mm.yyyy or natural text>\n"
               "• /myevents — list your events\n"
               "• /delete <id> — delete an event\n"
               "• /checktoday — run today’s check for you now\n"
               "• /language — change language"),
        "ru": ("Привет! Я напомню о событиях и расскажу погоду в этот день 🌤\n\n"
               "1) Укажите город: /setcity Москва\n"
               "2) Добавьте событие: /addevent Встреча с коллегой 20.10.2025\n"
               "3) Утром около 08:00 (ваш часовой пояс) пришлю сообщение.\n\n"
               "Команды: ⚙️\n"
               "• /setcity <город>\n"
               "• /addevent <название> <дд.мм.гггг или фраза>\n"
               "• /myevents — список событий\n"
               "• /delete <id> — удалить событие\n"
               "• /checktoday — проверить события на сегодня\n"
               "• /language — сменить язык")
    },
    "pick_lang_buttons": {
        "en": [["English 🇬🇧", "lang:en"], ["Русский 🇷🇺", "lang:ru"]],
        "ru": [["English 🇬🇧", "lang:en"], ["Русский 🇷🇺", "lang:ru"]],
    },
    "lang_saved": {"en": "Language set to English 🇬🇧", "ru": "Язык переключен на русский 🇷🇺"},
    "owm_missing": {"en": "OWM_API_KEY is not set on the server.", "ru": "OWM_API_KEY не задан на сервере."},
    "setcity_usage": {"en": "Usage: /setcity <city name>\nExample: /setcity Berlin",
                      "ru": "Использование: /setcity <город>\nПример: /setcity Москва"},
    "setcity_not_found": {"en": "Sorry, I couldn’t find that city. Try a different spelling?",
                          "ru": "Не удалось найти такой город. Попробуйте другое написание."},
    "setcity_ok": {"en": "City set to: {city} (timezone: {tz}).",
                   "ru": "Город установлен: {city} (часовой пояс: {tz})."},
    "addevent_usage": {"en": "Usage: /addevent <title> <dd.mm.yyyy or natural text>\nExample: /addevent Meeting next Friday",
                       "ru": "Использование: /addevent <название> <дд.мм.гггг или фраза>\nПример: /addevent Встреча следующую пятницу"},
    "addevent_set_city_first": {"en": "First set your city with /setcity <city>.",
                                "ru": "Сначала укажите город: /setcity <город>."},
    "addevent_need_date": {"en": "Please include a date like 20.10.2025 or a phrase like 'next Friday'.",
                           "ru": "Пожалуйста, укажите дату (например, 20.10.2025) или фразу типа «следующую пятницу»."},
    "addevent_past": {"en": "That date is in the past for your timezone. Choose a future date.",
                      "ru": "Эта дата уже прошла в вашем часовом поясе. Выберите будущую дату."},
    "addevent_ok": {"en": "Added event #{id}: “{title}” on {date}.",
                    "ru": "Добавлено событие #{id}: «{title}» на {date}."},
    "no_events": {"en": "No events yet. Add one with /addevent …",
                  "ru": "Событий пока нет. Добавьте с помощью /addevent …"},
    "myevents_line": {"en": "{mark} {idx}. {title} — {date}  (id {id})",
                      "ru": "{mark} {idx}. {title} — {date}  (id {id})"},
    "delete_usage": {"en": "Usage: /delete <event_id>", "ru": "Использование: /delete <id>"},
    "delete_ok": {"en": "Deleted.", "ru": "Удалено."},
    "delete_fail": {"en": "Couldn’t delete (wrong ID?).", "ru": "Не удалось удалить (неверный ID?)."},
    "checktoday_setcity_first": {"en": "First set your city with /setcity <city>.",
                                 "ru": "Сначала укажите город: /setcity <город>."},
    "checktoday_done": {"en": "Checked today for you.", "ru": "Проверка на сегодня выполнена."},
    "today_you_have": {"en": "Today you have **{title}**.", "ru": "Сегодня у вас **{title}**."},
    "weather_unavailable": {"en": "(Weather unavailable right now.)", "ru": "(Погода сейчас недоступна.)"},
    "advice_default": {"en": "enjoy your day 🙂", "ru": "хорошего дня 🙂"},
    "advice_umbrella": {"en": "take an umbrella ☔️", "ru": "возьмите зонт ☔️"},
    "advice_snow_shoes": {"en": "wear warm, waterproof shoes ❄️", "ru": "обуйтесь теплее, водонепроницаемая обувь ❄️"},
    "advice_very_cold": {"en": "dress very warmly (hat & gloves) 🧣", "ru": "оденьтесь очень тепло (шапка и перчатки) 🧣"},
    "advice_warm_coat": {"en": "wear a warm coat 🧥", "ru": "наденьте тёплое пальто/куртку 🧥"},
    "advice_light_jacket": {"en": "bring a light jacket 🧥", "ru": "возьмите лёгкую куртку 🧥"},
    "advice_comfy": {"en": "comfortable temps — a light layer is enough 👕", "ru": "комфортно — хватит лёгкого слоя 👕"},
    "advice_warm": {"en": "it’s warm — stay hydrated 💧", "ru": "жарковато — не забывайте пить воду 💧"},
    "advice_hot": {"en": "it’s hot — seek shade & hydrate 🧊", "ru": "очень жарко — держитесь в тени и пейте воду 🧊"},
    "advice_very_windy": {"en": "very windy — secure loose items & wear a windbreaker 🌬️",
                          "ru": "очень ветрено — наденьте ветрозащитную куртку 🌬️"},
    "advice_breezy": {"en": "quite breezy — a windbreaker could help 🌬️",
                      "ru": "ветрено — пригодится ветрозащитная куртка 🌬️"},
    "advice_overcast": {"en": "overcast skies — consider a layer ☁️", "ru": "пасмурно — прихватите дополнительный слой ☁️"},
    "advice_mostly_cloudy": {"en": "mostly cloudy ☁️", "ru": "облачно ☁️"},
    "w_temp": {"en": "• Temperature: {t}°C (feels like {fl}°C)", "ru": "• Температура: {t}°C (ощущается как {fl}°C)"},
    "w_temp_simple": {"en": "• Temperature: {t}°C", "ru": "• Температура: {t}°C"},
    "w_condition": {"en": "• Condition: {cond}", "ru": "• Состояние: {cond}"},
    "w_wind": {"en": "• Wind: {w} m/s", "ru": "• Ветер: {w} м/с"},
    "w_clouds": {"en": "• Cloudiness: {c}%", "ru": "• Облачность: {c}%"},
    "w_rain": {"en": "• Rain (last hour): {mm} mm", "ru": "• Осадки (за час): {mm} мм"},
    "w_snow": {"en": "• Snow (last hour): {mm} mm", "ru": "• Снег (за час): {mm} мм"},
}

def t(lang: str, key: str, **kwargs) -> str:
    lang = lang if lang in (LANG_EN, LANG_RU) else LANG_EN
    s = I18N[key][lang]
    return s.format(**kwargs) if kwargs else s

PICK_LANG_BUTTONS = I18N["pick_lang_buttons"]["en"]

def ensure_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise SystemExit(f"Please set {name} environment variable.")
    return val
