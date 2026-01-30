import re
from markupsafe import Markup, escape

def link_bible_verses(text):
    """
    Finds Bible references (e.g., John 3:16, Gen 1:1-5) and links them to BibleGateway.
    """
    if not text:
        return ""

    # Escape user content first to prevent XSS
    escaped_text = str(escape(text))

    pattern = r'\b((?:[1-3]\s)?[A-Z][a-z]+)\s+(\d+):(\d+(?:-\d+)?)'

    def replace_match(match):
        book = match.group(1)
        chapter = match.group(2)
        verse = match.group(3)
        full_ref = f"{book} {chapter}:{verse}"

        encoded_ref = full_ref.replace(" ", "+").replace(":", "%3A")
        url = f"https://www.biblegateway.com/passage/?search={encoded_ref}&version=NIV"

        return f'<a href="{url}" target="_blank" class="text-decoration-underline text-primary">{full_ref}</a>'

    linked_text = re.sub(pattern, replace_match, escaped_text)

    return Markup(linked_text)
