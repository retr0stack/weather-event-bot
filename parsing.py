import re
import dateparser
from datetime import date

DATE_RE = re.compile(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})")

def parse_event_args(text: str, tz_name: str, lang: str) -> tuple[str, date] | None:
    # 1) Explicit dd.mm.yyyy / dd-mm-yyyy / dd/mm/yyyy
    m = DATE_RE.search(text)
    if m:
        day, month, year = map(int, m.groups())
        try:
            d = date(year, month, day)
        except ValueError:
            return None
        title = (text[:m.start()] + text[m.end():]).strip().strip('"“”')
        return (title or ("Untitled event" if lang == "en" else "Без названия")), d

    # 2) Natural language (use user's timezone + language)
    settings = {
        "TIMEZONE": tz_name,
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    # IMPORTANT: pass languages via the parameter, not in settings
    langs = ["en"] if lang == "en" else ["ru"]
    dt = dateparser.parse(text, settings=settings, languages=langs)
    if not dt:
        return None

    parts = text.strip().strip('"“”').split()
    if len(parts) >= 2:
        candidates = [
            " ".join(parts[:-1]),
            " ".join(parts[:-2]) if len(parts) >= 3 else None,
            " ".join(parts[:-3]) if len(parts) >= 4 else None,
        ]
        title = next((c for c in candidates if c and len(c) >= 2), None) or ("Untitled event" if lang == "en" else "Без названия")
    else:
        title = "Untitled event" if lang == "en" else "Без названия"

    return title, dt.date()
