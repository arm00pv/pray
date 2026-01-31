from .bible_plan import get_plan_for_day

def get_todays_reading():
    from datetime import datetime
    day_of_year = datetime.now().timetuple().tm_yday

    # Use full year plan
    # Adjust for leap years or just cap at 365
    if day_of_year > 365: day_of_year = 365

    reading = get_plan_for_day(day_of_year)

    return {"plan_title": "Bible in a Year", "reading": reading}
