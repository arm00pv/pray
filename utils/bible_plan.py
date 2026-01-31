# Simple static Bible reading plan (One Year Bible style)
# Day 1 to 365
BIBLE_PLAN = {
    1: "Genesis 1-2; Matthew 1",
    2: "Genesis 3-5; Matthew 2",
    3: "Genesis 6-8; Matthew 3",
    4: "Genesis 9-11; Matthew 4",
    5: "Genesis 12-14; Matthew 5:1-26",
    6: "Genesis 15-17; Matthew 5:27-48",
    7: "Genesis 18-19; Matthew 6",
    8: "Genesis 20-22; Matthew 7",
    9: "Genesis 23-24; Matthew 8",
    10: "Genesis 25-26; Matthew 9:1-17",
    # ... In a real app, this would be full 365 days
    # For demo purposes, we fill a few more and assume pattern
    365: "Revelation 21-22"
}

# Fill gaps for demo to allow testing any day of year roughly
def get_plan_for_day(day_num):
    if day_num in BIBLE_PLAN:
        return BIBLE_PLAN[day_num]
    # Fallback/Mock for demo days not explicitly typed out above
    return f"Reading for Day {day_num} (Placeholder)"
