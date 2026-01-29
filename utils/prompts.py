from datetime import datetime

PROMPTS = [
    "What are you most grateful for today?",
    "Who is someone you need to forgive?",
    "What is a burden you need to give to God?",
    "Pray for a friend who is going through a hard time.",
    "Reflect on a recent blessing.",
    "Pray for your local church leaders.",
    "What is a fruit of the Spirit you want to grow in?",
    "Pray for someone you don't get along with.",
    "Thank God for His faithfulness in your life.",
    "Pray for wisdom in a decision you are facing."
]

def get_daily_prompt():
    """Returns a daily prayer prompt based on the day of the year."""
    day_of_year = datetime.now().timetuple().tm_yday
    index = day_of_year % len(PROMPTS)
    return PROMPTS[index]
