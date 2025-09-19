# Weather Event Bot (Telegram) --- README

A bilingual (English/ Russian) Telegram bot that lets users add
dated events and automatically sends them a morning message on the event
day with **local** weather advice (umbrella/jacket/etc.) based on
OpenWeatherMap.

This README walks you through **first-time setup** (including tokens),
**how to run**, **every bot feature**, **project structure**, **how
things work**, and **troubleshooting**.

------------------------------------------------------------------------

## Quick Start (first launch)

### 0) Create your Telegram bot (BotFather)

1.  In Telegram, search **@BotFather** → Start.
2.  Send `/newbot`, choose:
    -   **Name** (display name, e.g., *Weather Event Assistant*)
    -   **Username** ending with `bot` (e.g., `WeatherEventHelperBot`(already busy)
3.  BotFather replies with your **bot token**, e.g.\
    `1234567890:ABCdefGhIJKlmNoPQRstuVWxyZ`\
    Keep it safe. You'll use it as `TELEGRAM_BOT_TOKEN`.

------------------------------------------------------------------------

### 1) Get an OpenWeatherMap API key

1.  Create an account at **openweathermap.org**.
2.  Go to **My API keys** → generate a key.\
    You'll use it as `OWM_API_KEY`.

------------------------------------------------------------------------

### 2) Clone/download the project

Place the project on your device. The structure:

    weather_event_bot/
    ├─ bot.py
    ├─ config.py
    ├─ db.py
    ├─ handlers.py
    ├─ parsing.py
    ├─ tztools.py
    ├─ weather.py
    ├─ requirements.txt
    └─ bot.db (will be auto-created)

------------------------------------------------------------------------

### 3) Create a virtual environment & install dependencies

#### Windows (PowerShell)

``` powershell
cd "path\to\weather_event_bot"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### macOS / Linux (bash/zsh)

``` bash
cd path/to/weather_event_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` includes:

    python-telegram-bot[job-queue]==21.4
    aiohttp
    timezonefinder
    dateparser

------------------------------------------------------------------------

### 4) Provide your secrets (environment variables)

You must set **both** before running.

#### Windows (PowerShell)

``` powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
$env:OWM_API_KEY="YOUR_OPENWEATHER_KEY"
```

#### macOS / Linux

``` bash
export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
export OWM_API_KEY="YOUR_OPENWEATHER_KEY"
```

------------------------------------------------------------------------

### 5) Run the bot

``` bash
python bot.py
```

You should see:

    Bot is running (polling). Press Ctrl+C to stop.

Open Telegram → your bot (e.g., `t.me/WeatherEventHelperBot`) →
**Start**.

------------------------------------------------------------------------

## How to Use (User Guide)

### Language selection

-   On `/start`, the bot shows buttons:
    -   **English**
    -   **Русский**
-   You can switch anytime with `/language`.

### Set your city

-   Example:
    -   EN: `/setcity Berlin`
    -   RU: `/setcity Москва`
-   The bot:
    -   Geocodes your city via OpenWeatherMap Geo API.
    -   Detects **IANA timezone** (e.g., `Europe/Berlin`) from
        coordinates.
    -   Stores it with your user profile.
    -   Schedules a **daily 08:00 (local time)** job for your reminders.

### Add an event

-   **Fixed date**:
    -   EN/RU: `/addevent Meeting with coworker 20.10.2025`
-   **Natural language date** (automatically parsed in your language):
    -   EN: `/addevent Lesson next friday`
    -   RU: `/addevent Встреча следующую пятницу`
    -   EN: `/addevent Coffee tomorrow`
    -   EN: `/addevent Trip in 2 weeks`

> The bot accepts either `dd.mm.yyyy` (also `dd-mm-yyyy`/`dd/mm/yyyy`)
> **or** a natural phrase.

### List events

-   `/myevents`\
    Shows your upcoming events in date order with a friendly index and
    the real `(id X)` used for deletion.

### Delete an event

-   `/delete 5`\
    Deletes the event with database ID **5** (see `/myevents`).

### Manually check today

-   `/checktoday`\
    Runs the same logic as the morning job **right now**:
    -   If you have events **today** (in your local timezone):
        -   Fetches **current** weather for your city.
        -   Sends advice and a weather breakdown.
    -   Marks those events as **notified** (won't repeat).

### Daily reminder behavior

-   Every day at **08:00 in your city's timezone**:
    -   The bot finds **your events scheduled for 'today'** (again in
        your timezone).
    -   Fetches **current weather** (not forecast) from OpenWeatherMap.
    -   Sends a message like:

    ```{=html}
    <!-- -->
    ```
        Today you have **your event**.
        take an umbrella ☔️ • bring a light jacket 🧥

        • Temperature: xx°C (feels like xx°C)
        • Condition: light rain
        • Wind: xx m/s
        • Cloudiness: xx%
        • Rain (last hour): xx.xx mm

------------------------------------------------------------------------

## Project Structure

    weather_event_bot/
    ├─ bot.py            # Wires handlers, runs polling, restores jobs
    ├─ config.py         # Logging, language changer, helpers
    ├─ db.py             # SQLite models/helpers + migrations
    ├─ handlers.py       # Telegram command, callback handlers, scheduling
    ├─ parsing.py        # Date parsing, natural language
    ├─ tztools.py        # Timezone detection from lat/lon
    ├─ weather.py        # OpenWeather calls + advice generation + formatting
    ├─ requirements.txt  # Dependencies
    └─ bot.db            # SQLite database (auto-created)

------------------------------------------------------------------------

## Troubleshooting

### Bot doesn't respond to anything

-   Ensure you're running with correct **token** and talking to the
    **same bot** (`t.me/<username>` BotFather created).
-   Verify network: the console should show polling logs.
-   Make sure **only one instance** of the bot is running (kill extra
    `python.exe`).

### `/ping` works, others don't

-   You might be in a **group**; test in a **direct chat** first.
-   Watch console logs: handlers log lines like `HIT /addevent: ...`.\
    If you don't see them, the commands aren't reaching the right
    handler.

### "No JobQueue set up" warning / scheduling fails

-   Install the extra:\
    `pip install "python-telegram-bot[job-queue]==21.4"`

### `ModuleNotFoundError: ...`

-   You installed into a different interpreter than the one running the
    bot.

-   In terminal, check:

    ``` bash
    python -c "import sys; print(sys.executable)"
    pip -V
    python -m pip show dateparser
    ```

    Paths should point to your project's `.venv`. If not, activate the
    venv or switch PyCharm to the right interpreter.

### Reset database (start fresh)

-   Stop the bot.
-   Delete `bot.db` (or rename it for backup).
-   Start the bot again; it will recreate an empty DB.

------------------------------------------------------------------------

## Credits

Built with: - [python-telegram-bot 21.x](https://docs.python-telegram-bot.org/) - [OpenWeatherMap APIs](https://openweathermap.org/api) - [timezonefinder](https://github.com/jannikmi/timezonefinder) - [dateparser](https://dateparser.readthedocs.io/)
