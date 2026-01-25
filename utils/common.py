import requests
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from flask import current_app

# Ensure NLTK data is available
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    try:
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('averaged_perceptron_tagger', quiet=True)

# Call it on import or handle it gracefully
download_nltk_data()

def get_geolocation(ip):
    if ip in ['127.0.0.1', '::1', 'localhost']:
        return {
            "status": "success",
            "country": "Localland",
            "countryCode": "LL",
            "region": "LO",
            "regionName": "Localhost",
            "city": "My Computer",
            "zip": "00000",
            "lat": 0.0,
            "lon": 0.0,
            "timezone": "UTC",
            "isp": "Loopback",
            "org": "Loopback",
            "as": "AS0000 NA",
            "query": ip
        }

    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = response.json()
        if data.get('status') == 'success':
            return data
        return None
    except Exception as e:
        print(f"Error fetching geolocation: {e}")
        return None

def extract_tags(text, locale='en'):
    """
    Extracts keywords/petitions from text using NLTK.
    Returns a list of strings (tags).
    """
    if not text:
        return []

    try:
        # Map locale to NLTK language
        lang_map = {
            'en': 'english',
            'es': 'spanish'
        }
        language = lang_map.get(locale, 'english')

        # Tokenize
        words = word_tokenize(text.lower())

        # Remove stopwords and non-alphabetic tokens
        try:
            stop_words = set(stopwords.words(language))
        except OSError:
             # Fallback if language not found
             stop_words = set(stopwords.words('english'))

        # Add some common prayer words that are not petitions themselves
        common_prayer_words = {
            'english': ['god', 'lord', 'pray', 'prayer', 'please', 'amen', 'help', 'ask', 'give', 'thank', 'thanks', 'want'],
            'spanish': ['dios', 'señor', 'orar', 'oracion', 'por favor', 'amen', 'ayuda', 'pedir', 'dar', 'gracias', 'quiero']
        }

        stop_words.update(common_prayer_words.get(language, []))

        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

        # POS Tagging to find nouns
        # Note: NLTK POS tagger is primarily trained for English.
        # For Spanish, we might need a different tagger or just skip POS filtering and rely on stopwords.
        # For simplicity in this demo, we'll try POS tagging for English, and for Spanish just take filtered words
        # (or assume basic POS accuracy).

        tags = []
        if language == 'english':
            tagged = nltk.pos_tag(filtered_words)
            tags = [word for word, tag in tagged if tag.startswith('NN')]
        else:
            # Simple fallback for non-English: just return filtered words (maybe length filter)
            tags = [word for word in filtered_words if len(word) > 3]

        # Return unique tags
        return list(set(tags))
    except Exception as e:
        print(f"Error extracting tags: {e}")
        return []

import re
import unicodedata

class ProfanityFilter:
    def __init__(self):
        # Expanded list including English, Spanish, slang, and common compounds
        self.bad_words = [
            'badword', 'swear', 'spam',
            # Spanish
            'mierda', 'puta', 'puto', 'cabron', 'cabrón', 'coño', 'joder', 'estupido', 'estúpido',
            'idiota', 'imbecil', 'imbécil', 'verga', 'pendejo', 'chingar', 'pinche', 'mamaguevo',
            'gonorrea', 'malparido',
            # English
            'fuck', 'shit', 'bitch', 'asshole', 'bastard', 'damn', 'cunt', 'dick', 'pussy',
            'faggot', 'nigger', 'slut', 'whore', 'cock', 'tits'
        ]
        # Regex for compounds/evasions (e.g., a$$hole, f.u.c.k) - Simplified for demo
        self.patterns = [
            r'f[u*]+c+k',
            r's[h*]+i+t',
            r'b[i*]+t+c+h',
            r'a+s+s+',
        ]

    def normalize_text(self, text):
        # Remove accents
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

    def is_profane(self, text):
        if not text:
            return False

        text_lower = text.lower()
        normalized_text = self.normalize_text(text_lower)

        for word in self.bad_words:
            word_lower = word.lower()
            if word_lower in text_lower or self.normalize_text(word_lower) in normalized_text:
                return True

        # Check patterns
        for pattern in self.patterns:
            if re.search(pattern, text_lower):
                return True

        return False

def validate_password_strength(password):
    """
    Validates password strength.
    Returns (bool, list_of_errors)
    Requirements: 8+ chars, 1 upper, 1 lower, 1 number
    """
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number.")

    return len(errors) == 0, errors

def send_email(to, subject, text, html=None):
    api_key = current_app.config.get('MAILGUN_API_KEY')
    domain = current_app.config.get('MAILGUN_DOMAIN')
    base_url = current_app.config.get('MAILGUN_BASE_URL')

    if not api_key or not domain:
        print(f"[MOCK EMAIL] To: {to}, Subject: {subject}, Body: {text}")
        return True

    try:
        data = {
            "from": f"Praying Diary <mailgun@{domain}>",
            "to": [to],
            "subject": subject,
            "text": text
        }
        if html:
            data["html"] = html

        response = requests.post(
            f"{base_url}/{domain}/messages",
            auth=("api", api_key),
            data=data
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
