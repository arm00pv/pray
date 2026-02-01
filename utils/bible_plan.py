BIBLE_PLAN = {
    1: "Genesis 1-2; Matthew 1",
    2: "Genesis 3-5; Matthew 2",
    3: "Genesis 6-8; Matthew 3",
    365: "Revelation 21-22"
}

def get_plan_for_day(day_num):
    return BIBLE_PLAN.get(day_num, f"Reading for Day {day_num}")
