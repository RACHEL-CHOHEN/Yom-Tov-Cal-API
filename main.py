# main.py
from fastapi import FastAPI, Request
import requests
from datetime import datetime, timedelta

app = FastAPI()

HOLIDAYS = {
    ("תשרי", 1): "ראש השנה",
    ("תשרי", 2): "ראש השנה",
    ("תשרי", 10): "יום כיפור",
    ("תשרי", 15): "סוכות",
    ("תשרי", 22): "שמחת תורה",
    ("ניסן", 15): "פסח",
    ("ניסן", 21): "שביעי של פסח",
    ("סיון", 6): "שבועות"
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

def get_day_info(greg_date: datetime):
    hebcal_data = get_hebrew_date(greg_date)
    hebrew_date = hebcal_data.get("hebrew")
    heb_day = hebcal_data.get("hd")
    heb_month = hebcal_data.get("hm")
    weekday = greg_date.weekday()  # 6 = Saturday

    holiday_name = HOLIDAYS.get((heb_month, heb_day))
    is_holiday = holiday_name is not None
    is_shabbat = weekday == 6  # רק שבת = 6

    # בדיקת ערב חג
    next_day = greg_date + timedelta(days=1)
    next_day_data = get_hebrew_date(next_day)
    next_hd = next_day_data.get("hd")
    next_hm = next_day_data.get("hm")
    next_holiday_name = HOLIDAYS.get((next_hm, next_hd))

    is_erev_hag = next_holiday_name is not None
    erev_hag_name = next_holiday_name if is_erev_hag else None

    if is_holiday:
        day_type = f"חג ({holiday_name})"
    elif is_erev_hag:
        day_type = f"ערב חג ({erev_hag_name})"
    elif is_shabbat:
        day_type = "שבת"
    else:
        day_type = "חול"

    return {
        "hebrew_date": hebrew_date,
        "day_type": day_type,
        "is_holiday": is_holiday,
        "is_shabbat": is_shabbat,
        "holiday_name": holiday_name if is_holiday else ("שבת" if is_shabbat else None)
    }

def find_next_day(greg_date: datetime, target_type: str):
    for i in range(1, 30):
        check_date = greg_date + timedelta(days=i)
        info = get_day_info(check_date)
        if target_type == "חול" and not info["is_shabbat"] and not info["is_holiday"]:
            return check_date.strftime("%Y-%m-%d")
        if target_type == "קודש" and (info["is_shabbat"] or info["is_holiday"]):
            return {
                "date": check_date.strftime("%Y-%m-%d"),
                "name": info["holiday_name"]
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

    today_info = get_day_info(date_obj)
    next_weekday = find_next_day(date_obj, "חול")
    next_holy_day = find_next_day(date_obj, "קודש")

    return {
        "input_date": date_str,
        "hebrew_date": today_info["hebrew_date"],
        "day_type": today_info["day_type"],
        "next_weekday": next_weekday,
        "next_holy_day_date": next_holy_day["date"] if next_holy_day else None,
        "next_holy_day_name": next_holy_day["name"] if next_holy_day else None
    }
