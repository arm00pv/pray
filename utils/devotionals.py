import random
from datetime import datetime

# Static list of devotionals for MVP (In real app, fetch from API)
DEVOTIONALS = [
    {
        "title": "Trusting in God's Plan",
        "scripture": "Jeremiah 29:11",
        "content": "God has a plan for you, plans to prosper you and not to harm you, plans to give you hope and a future. Trust in His timing."
    },
    {
        "title": "The Power of Prayer",
        "scripture": "James 5:16",
        "content": "The prayer of a righteous person is powerful and effective. Do not underestimate the impact of your prayers today."
    },
    {
        "title": "Walking by Faith",
        "scripture": "2 Corinthians 5:7",
        "content": "For we live by faith, not by sight. Even when the path ahead is unclear, trust that He is guiding your steps."
    },
    {
        "title": "Finding Peace",
        "scripture": "Philippians 4:6-7",
        "content": "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God."
    },
    {
        "title": "Strength in Weakness",
        "scripture": "2 Corinthians 12:9",
        "content": "My grace is sufficient for you, for my power is made perfect in weakness. Rely on His strength today."
    }
]

def get_daily_devotional():
    """Returns a daily devotional based on the day of the year."""
    day_of_year = datetime.now().timetuple().tm_yday
    index = day_of_year % len(DEVOTIONALS)
    return DEVOTIONALS[index]
