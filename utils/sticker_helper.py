def count_stickers(stickers_str):
    """
    Parses a comma-separated string of stickers/emojis and returns a list of dicts with count.
    e.g. "🙏,🙏,❤️" -> [{'icon': '🙏', 'count': 2}, {'icon': '❤️', 'count': 1}]
    """
    if not stickers_str:
        return []

    parts = stickers_str.split(',')
    counts = {}
    for part in parts:
        p = part.strip()
        if p:
            counts[p] = counts.get(p, 0) + 1

    # Convert to list
    result = []
    for icon, count in counts.items():
        result.append({'icon': icon, 'count': count})

    return result
