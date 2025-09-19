import os
from datetime import datetime, time as dt_time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, JobQueue, filters

from config import log, t, LANG_EN, PICK_LANG_BUTTONS
from db import (
    get_user, set_user_lang, set_user_city,
    add_event, list_events, delete_event, get_events_for_date, mark_notified,
    list_all_users
)
from tztools import detect_timezone_name, tz_now
from parsing import parse_event_args
from weather import geocode_city, fetch_current_weather, make_advice, format_weather_list

def row_has(row, key: str) -> bool:
    try:
        return key in row.keys()
    except Exception:
        return False

def user_lang_or_default(user, default="en"):
    return user["lang"] if (user and row_has(user, "lang") and user["lang"]) else default

# ---------- UI helpers ----------
def lang_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=txt, callback_data=data)] for txt, data in PICK_LANG_BUTTONS]
    return InlineKeyboardMarkup(rows)

# ---------- Handlers ----------
async def cmd_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)
    await update.effective_message.reply_text(t(lang, "start_pick_lang"), reply_markup=lang_keyboard())

async def on_language_pick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not q.data.startswith("lang:"):
        return
    new_lang = q.data.split(":", 1)[1]
    set_user_lang(q.from_user.id, new_lang)
    await q.edit_message_text(t(new_lang, "lang_saved"))
    await context.bot.send_message(chat_id=q.from_user.id, text=t(new_lang, "start_help"))

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /start: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    if not user or not row_has(user, "lang"):
        await update.effective_message.reply_text(t(LANG_EN, "start_pick_lang"), reply_markup=lang_keyboard())
        return
    await update.effective_message.reply_text(t(user["lang"], "start_help"))

async def cmd_setcity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /setcity: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)

    api_key = os.getenv("OWM_API_KEY")
    if not api_key:
        await update.effective_message.reply_text(t(lang, "owm_missing"))
        return
    if not context.args:
        await update.effective_message.reply_text(t(lang, "setcity_usage"))
        return

    city_input = " ".join(context.args)
    async with aiohttp.ClientSession() as session:
        geo = await geocode_city(session, api_key, city_input)
    if not geo:
        await update.effective_message.reply_text(t(lang, "setcity_not_found"))
        return

    tz_name = detect_timezone_name(geo["lat"], geo["lon"])
    set_user_city(update.effective_user.id, geo["name"], geo["lat"], geo["lon"], tz_name)
    await update.effective_message.reply_text(t(lang, "setcity_ok", city=geo["name"], tz=tz_name))
    await schedule_user_daily_job(context.job_queue, update.effective_user.id, tz_name)

async def cmd_addevent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /addevent: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)
    if not user:
        await update.effective_message.reply_text(t(lang, "addevent_set_city_first"))
        return
    parts = update.effective_message.text.split(" ", 1)
    if len(parts) == 1 or not parts[1].strip():
        await update.effective_message.reply_text(t(lang, "addevent_usage"))
        return
    args_text = parts[1].strip()
    parsed = parse_event_args(args_text, user["timezone"], lang)
    if not parsed:
        await update.effective_message.reply_text(t(lang, "addevent_need_date"))
        return
    title, d = parsed
    if d < tz_now(user["timezone"]).date():
        await update.effective_message.reply_text(t(lang, "addevent_past"))
        return
    event_id = add_event(update.effective_user.id, title, d)
    await update.effective_message.reply_text(t(lang, "addevent_ok", id=event_id, title=title, date=d.strftime('%d.%m.%Y')))

async def cmd_myevents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /myevents: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)
    rows = list_events(update.effective_user.id)
    if not rows:
        await update.effective_message.reply_text(t(lang, "no_events"))
        return
    lines = []
    for idx, r in enumerate(rows[:100], start=1):
        mark = "✅" if r["notified"] else "⏳"
        dt_text = datetime.strptime(r["event_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        lines.append(t(lang, "myevents_line", mark=mark, idx=idx, title=r["title"], date=dt_text, id=r["id"]))
    await update.effective_message.reply_text("\n".join(lines))

async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /delete: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text(t(lang, "delete_usage"))
        return
    ok = delete_event(update.effective_user.id, int(context.args[0]))
    await update.effective_message.reply_text(t(lang, "delete_ok") if ok else t(lang, "delete_fail"))

async def cmd_checktoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("HIT /checktoday: %r", update.effective_message.text)
    user = get_user(update.effective_user.id)
    lang = user_lang_or_default(user, LANG_EN)
    if not user:
        await update.effective_message.reply_text(t(lang, "checktoday_setcity_first"))
        return
    await run_daily_for_user(context, user)
    await update.effective_message.reply_text(t(lang, "checktoday_done"))

async def cmd_ping(update, context):
    await update.effective_message.reply_text("pong (replied successfully)")

async def debug_echo(update, context):
    log.debug("Got update: %s", update)

# ---------- Scheduling ----------
from telegram.ext import JobQueue
from zoneinfo import ZoneInfo
import aiohttp

async def schedule_user_daily_job(job_queue: JobQueue, user_id: int, tz_name: str):
    if job_queue is None:
        log.error('JobQueue not available. Install: pip install "python-telegram-bot[job-queue]"')
        return
    name = f"daily-{user_id}"
    for job in job_queue.get_jobs_by_name(name):
        job.schedule_removal()
    job_queue.run_daily(
        callback=user_daily_job_callback,
        time=dt_time(hour=8, minute=0, tzinfo=ZoneInfo(tz_name)),
        name=name,
        data={"user_id": user_id},
    )
    log.info("Scheduled daily job for user %s at 08:00 %s", user_id, tz_name)

async def user_daily_job_callback(context: ContextTypes.DEFAULT_TYPE):
    user_id = context.job.data["user_id"]
    user = get_user(user_id)
    if not user:
        return
    await run_daily_for_user(context, user)

async def run_daily_for_user(context: ContextTypes.DEFAULT_TYPE, user_row):
    import os
    owm_key = os.getenv("OWM_API_KEY")
    if not owm_key:
        log.error("OWM_API_KEY missing; cannot fetch weather.")
        return
    lang = user_lang_or_default(user_row, LANG_EN)
    local_today = tz_now(user_row["timezone"]).date().isoformat()
    due = get_events_for_date(user_row["user_id"], local_today)
    if not due:
        log.info("No events today for user %s", user_row["user_id"])
        return
    async with aiohttp.ClientSession() as session:
        weather = await fetch_current_weather(session, owm_key, user_row["lat"], user_row["lon"])
    for e in due:
        if weather:
            advice = make_advice(weather, lang)
            details = format_weather_list(weather, lang)
            message = f"{t(lang, 'today_you_have', title=e['title'])}\n{advice}\n\n{details}"
        else:
            message = f"{t(lang, 'today_you_have', title=e['title'])}\n{t(lang, 'weather_unavailable')}"
        try:
            await context.bot.send_message(chat_id=user_row["user_id"], text=message, parse_mode="Markdown")
        except Exception as ex:
            log.exception("Failed to send to %s: %s", user_row["user_id"], ex)
        mark_notified(e["id"])
