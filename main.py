# main.py
from fastapi import FastAPI, Request
import requests
from datetime import datetime, timedelta

app = FastAPI()

HOLIDAYS = {
    ("Tishrei", 1): "ראש השנה",
    ("Tishrei", 2): "ראש השנה",
    ("Tishrei", 10): "יום כיפור",
    ("Tishrei", 15): "סוכות",
    ("Tishrei", 22): "שמחת תורה",
    ("Nisan", 15): "פסח",
    ("Nisan", 21): "שביעי של פסח",
    ("Sivan", 6): "שבועות"
}


def get_hebrew_date(greg_date: datetime):
    url = "https://www.hebcal.com/converter"
    params = {
        "cfg": "json",
        "gy": greg_date.year,
        "gm": greg_date.month,
        "gd": greg_date.day,
        "g2h": 1
    }
    response = requests.get(url, params=params)
    return response.json()


def determine_day_type(date: datetime):
    heb = get_hebrew_date(date)
    hd, hm = heb.get("hd"), heb.get("hm")
    hebrew_date = heb.get("hebrew")
    weekday = date.weekday()  # 5 = Saturday

    is_holiday = (hm, hd) in HOLIDAYS
    holiday_name = HOLIDAYS.get((hm, hd))
    is_shabbat = weekday == 5

    # ערב חג
    next_day = date + timedelta(days=1)
    next = get_hebrew_date(next_day)
    next_hd, next_hm = next.get("hd"), next.get("hm")
    next_weekday = next_day.weekday()
    next_is_holiday = (next_hm, next_hd) in HOLIDAYS
    next_holiday_name = HOLIDAYS.get((next_hm, next_hd))
    next_is_shabbat = next_weekday == 5

    parts = []
    if is_shabbat:
        parts.append("שבת")
    elif next_is_shabbat:
        parts.append("ערב שבת")
    if is_holiday:
        parts.append(f"חג ({holiday_name})")
    elif next_is_holiday:
        parts.append(f"ערב חג ({next_holiday_name})")

    day_type = " ".join(parts) if parts else "חול"

    return {
        "hebrew_date": hebrew_date,
        "day_type": day_type,
        "is_holiday": is_holiday,
        "is_shabbat": is_shabbat,
        "heb": heb,
    }


def find_next_weekday(from_date: datetime):
    close_holidays_date = []
    for i in range(1, 7):
        date = from_date + timedelta(days=i)
        info = determine_day_type(date)
        heb=info["heb"]
        heDateParts = heb.get("heDateParts")
        if not info["is_holiday"] and not info["is_shabbat"]:
            return {
                "next_yom_hol": date.strftime("%Y-%m-%d"),
                "close_holidays_date": close_holidays_date,
            }
        else:
            close_holidays_date.append(heDateParts) 
    return None


def find_next_holy_day(from_date: datetime):
    for i in range(1, 8):  # עד 7 ימים קדימה בלבד
        date = from_date + timedelta(days=i)
        info = determine_day_type(date)
        if info["is_holiday"] or info["is_shabbat"]:
            return {
                "date": date.strftime("%Y-%m-%d"),
                "name": info["day_type"]
            }
    return None


@app.post("/date-info")
async def date_info(req: Request):
    body = await req.json()
    date_str = body.get("date")
    if not date_str:
        return {"error": "Missing 'date' parameter"}

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    today_info = determine_day_type(date_obj)
    next_weekday = find_next_weekday(date_obj)
    next_holy = find_next_holy_day(date_obj)

    return {
        "input_date": date_str,
        "hebrew_date_from heb_cal": today_info["heb"],
        "day_type": today_info["day_type"],
        "close_holy_days_heb_date": next_weekday["close_holidays_date"],
        "next_weekday_not_yov_tov": next_weekday["next_yom_hol"],
        "next_holy_day_date": next_holy["date"] if next_holy else None,
        "next_holy_day_name": next_holy["name"] if next_holy else None
    }
