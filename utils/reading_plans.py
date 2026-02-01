READING_PLANS = {
    "gospels_90": {
        "title": "Gospels in 90 Days",
        "days": {
            1: "Matthew 1-2",
            2: "Matthew 3-4",
            3: "Matthew 5-6",
            # ... truncated for demo ...
            90: "John 20-21"
        }
    }
}

def get_todays_reading():
    # Simple day of year logic
    from datetime import datetime
    day_of_year = datetime.now().timetuple().tm_yday

    # Cycle through 90 days
    day_num = (day_of_year % 90) + 1

    plan = READING_PLANS['gospels_90']
    reading = plan['days'].get(day_num, "Psalms 1") # Fallback

    return {"plan_title": plan['title'], "reading": reading}
