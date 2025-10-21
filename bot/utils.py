import re
# Détection de langue
from langdetect import detect, DetectorFactory,LangDetectException
DetectorFactory.seed = 0


def detect_language(text):
    """Détection améliorée du wolof avec patterns + mots-clés"""
    text_lower = text.lower().strip()
    wolof_words = {'lan','lu','naka','ndax','ana','kañ','fan','ñaata',
                   'def','dem','jël','wax','gis','degg','lekk','tudd','jënd',
                   'fey','jëfandikoo','woneel','bind','mu','nga','dafa','nag',
                   'ci','bu','ngir','ak','am','yow','man','ñu','ñoom','kay','yaa','daa',
                   'baax','bés','bëgg','jamm','mag','ñu','nit','xaalis','goor','jigeen',
                   'xale','doom','njool','wareef','suba','liggeey','yalla','jërejëf',
                   'yoon','benn','ñaar','ñett','déedéet','waaw','rekk','itam','donc',
                   'walla','mangi','damaa','dama','amna','amoon','mooy','gayi','dugal',
                   'tann','woneel','sofer','noo','sa','seen'}
    wolof_patterns = [
        r'\b(d|n|l|m)a(fa|g|nga|mu)\b',
        r'\bng(a|ir|i)\b',
        r'\b(j|g)ë(l|nd|fandik)',
        r'\bci\s+\w+\s+(yi|bi|wi)',
        r'\bak\b',
        r'\bmooy\b',
        r'\brekk\b',
        r'\bndax\b'
    ]
    words = re.findall(r'\b\w+\b', text_lower)
    wolof_count = sum(1 for word in words if word in wolof_words)
    pattern_matches = sum(1 for pattern in wolof_patterns if re.search(pattern, text_lower))
    total_words = len(words)
    if total_words == 0:
        return 'fr'
    wolof_ratio = wolof_count / total_words
    if wolof_ratio >= 0.25 or pattern_matches >= 2 or wolof_count >= 3:
        return 'wo'
    if any(text_lower.startswith(q) for q in ['lu mooy', 'lan la', 'naka nga', 'ndax ', 'noo tudd']):
        return 'wo'
    try:
        lang = detect(text)
        if lang == 'en':
            return 'en'
        elif lang in ['fr','unknown']:
            return 'fr'
        return 'fr'
    except LangDetectException:
        return 'fr'