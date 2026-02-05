import requests
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

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

def extract_tags(text):
    """
    Extracts keywords/petitions from text using NLTK.
    Returns a list of strings (tags).
    """
    if not text:
        return []

    try:
        # Tokenize
        words = word_tokenize(text.lower())

        # Remove stopwords and non-alphabetic tokens
        stop_words = set(stopwords.words('english'))
        # Add some common prayer words that are not petitions themselves
        stop_words.update(['god', 'lord', 'pray', 'prayer', 'please', 'amen', 'help', 'ask', 'give', 'thank', 'thanks', 'want'])

        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]

        # POS Tagging to find nouns
        tagged = nltk.pos_tag(filtered_words)

        # Filter for Nouns (NN, NNS, NNP, NNPS)
        tags = [word for word, tag in tagged if tag.startswith('NN')]

        # Return unique tags
        return list(set(tags))
    except Exception as e:
        print(f"Error extracting tags: {e}")
        return []
