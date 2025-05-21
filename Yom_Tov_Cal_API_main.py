# main.py
from fastapi import FastAPI, Request
import requests
from datetime import datetime, timedelta

app = FastAPI()

def get_hebrew_date(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    url = "https://www.hebcal.com/converter"
    params = {
        "cfg": "json",
        "gy": date_obj.year,
        "gm": date_obj.month,
        "gd": date_obj.day,
        "g2h": 1
    }
    response = requests.get(url, params=params)
    return response.json()

def get_day_type(events):
    if not events:
        return "חול"
    if any("Shabbat" in e or "שבת" in e for e in events):
        return "שבת"
    if any("Erev" in e or "ערב חג" in e for e in events):
        return "ערב חג"
    if any("Yom Tov" in e or "חג" in e for e in events):
        return "חג"
    return "חול"

@app.post("/date-info")
async def date_info(req: Request):
    body = await req.json()
    date_str = body.get("date")
    if not date_str:
        return {"error": "Missing date"}

    result = get_hebrew_date(date_str)
    day_type = get_day_type(result.get("events", []))

    next_weekday = None
    next_holy_day = None
    for i in range(1, 15):
        new_date = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=i)
        res = get_hebrew_date(new_date.strftime('%Y-%m-%d'))
        events = res.get("events", [])
        day_type_next = get_day_type(events)
        if not next_weekday and day_type_next == "חול":
            next_weekday = new_date.strftime('%Y-%m-%d')
        if not next_holy_day and day_type_next in ["שבת", "חג"]:
            next_holy_day = f"{new_date.strftime('%Y-%m-%d')} ({day_type_next})"
        if next_weekday and next_holy_day:
            break

    return {
        "input_date": date_str,
        "hebrew_date": result.get("hebrew"),
        "day_type": day_type,
        "next_weekday": next_weekday,
        "next_holy_day": next_holy_day
    }
