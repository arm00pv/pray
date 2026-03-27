import random

VERSES = [
    {
        "en": {"text": "For I know the plans I have for you, declares the Lord, plans for welfare and not for evil, to give you a future and a hope.", "ref": "Jeremiah 29:11"},
        "es": {"text": "Porque yo sé los pensamientos que tengo acerca de vosotros, dice Jehová, pensamientos de paz, y no de mal, para daros el fin que esperáis.", "ref": "Jeremías 29:11"}
    },
    {
        "en": {"text": "I can do all things through him who strengthens me.", "ref": "Philippians 4:13"},
        "es": {"text": "Todo lo puedo en Cristo que me fortalece.", "ref": "Filipenses 4:13"}
    },
    {
        "en": {"text": "The Lord is my shepherd; I shall not want.", "ref": "Psalm 23:1"},
        "es": {"text": "Jehová es mi pastor; nada me faltará.", "ref": "Salmos 23:1"}
    },
    {
        "en": {"text": "Trust in the Lord with all your heart, and do not lean on your own understanding.", "ref": "Proverbs 3:5"},
        "es": {"text": "Fíate de Jehová de todo tu corazón, Y no te apoyes en tu propia prudencia.", "ref": "Proverbios 3:5"}
    },
    {
        "en": {"text": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.", "ref": "Romans 8:28"},
        "es": {"text": "Y sabemos que a los que aman a Dios, todas las cosas les ayudan a bien, esto es, a los que conforme a su propósito son llamados.", "ref": "Romanos 8:28"}
    },
    {
        "en": {"text": "Be strong and courageous. Do not be frightened, and do not be dismayed, for the Lord your God is with you wherever you go.", "ref": "Joshua 1:9"},
        "es": {"text": "Mira que te mando que te esfuerces y seas valiente; no temas ni desmayes, porque Jehová tu Dios estará contigo en dondequiera que vayas.", "ref": "Josué 1:9"}
    },
    {
        "en": {"text": "Cast all your anxiety on him because he cares for you.", "ref": "1 Peter 5:7"},
        "es": {"text": "Echando toda vuestra ansiedad sobre él, porque él tiene cuidado de vosotros.", "ref": "1 Pedro 5:7"}
    },
    {
        "en": {"text": "But those who hope in the Lord will renew their strength. They will soar on wings like eagles; they will run and not grow weary, they will walk and not be faint.", "ref": "Isaiah 40:31"},
        "es": {"text": "Pero los que esperan a Jehová tendrán nuevas fuerzas; levantarán alas como las águilas; correrán, y no se cansarán; caminarán, y no se fatigarán.", "ref": "Isaías 40:31"}
    },
    {
        "en": {"text": "Rejoice always, pray continually, give thanks in all circumstances; for this is God’s will for you in Christ Jesus.", "ref": "1 Thessalonians 5:16-18"},
        "es": {"text": "Estad siempre gozosos. Orad sin cesar. Dad gracias en todo, porque esta es la voluntad de Dios para con vosotros en Cristo Jesús.", "ref": "1 Tesalonicenses 5:16-18"}
    },
    {
        "en": {"text": "Peace I leave with you; my peace I give you. I do not give to you as the world gives. Do not let your hearts be troubled and do not be afraid.", "ref": "John 14:27"},
        "es": {"text": "La paz os dejo, mi paz os doy; yo no os la doy como el mundo la da. No se turbe vuestro corazón, ni tenga miedo.", "ref": "Juan 14:27"}
    }
]

import datetime

def get_random_verse(locale='en', seed_key=None):
    """
    Returns a random verse.
    If seed_key is provided, uses it to seed the RNG for stability (e.g., per user per day).
    """
    rng = random.Random()

    if seed_key:
        # Create a stable seed based on date and user key
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        full_seed_str = f"{today_str}-{seed_key}"
        # Use hashlib to ensure a consistent integer seed
        import hashlib
        seed_int = int(hashlib.sha256(full_seed_str.encode('utf-8')).hexdigest(), 16)
        rng.seed(seed_int)

    verse_data = rng.choice(VERSES)

    # Default to english if locale not found
    lang = locale if locale in ['en', 'es'] else 'en'
    return verse_data[lang]
