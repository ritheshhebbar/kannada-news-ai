import re
import unicodedata
from typing import List, Tuple

# Mapping of Kannada numerals to ASCII digits
KANNADA_DIGIT_MAP = str.maketrans({
    '೦': '0', '೧': '1', '೨': '2', '೩': '3', '೪': '4',
    '೫': '5', '೬': '6', '೭': '7', '೮': '8', '೯': '9'
})

def normalize_kannada_text(text: str) -> str:
    """Normalize Kannada text to Unicode NFC while preserving meaningful conjunct characters.
    
    Preserves Zero Width Joiner (U+200D) and Zero Width Non-Joiner (U+200C).
    Removes extraneous whitespace and formatting artifacts.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    # Normalize multiple whitespace to single space, while preserving newlines
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    normalized = re.sub(r'\n\s*\n+', '\n\n', normalized)
    return normalized.strip()

def split_kannada_sentences(text: str) -> List[str]:
    """Split Kannada news text into sentences while respecting Indic punctuation and abbreviations.
    
    Handles danda (।), double danda (॥), standard period (.), question marks, and exclamation marks.
    Protects common abbreviations like ಡಾ. (Dr.), ಪ್ರೊ. (Prof.), ಎಂ. (M.), ಬಿ. (B.), etc.
    """
    if not text:
        return []

    # Protect common initials / abbreviations with a placeholder
    protected = text
    abbrevs = [
        ("ಡಾ.", "__DR__"),
        ("ಪ್ರೊ.", "__PROF__"),
        ("ಶ್ರೀ.", "__SHRI__"),
        ("ಎಂ. ಬಿ.", "__MB__"),
        ("ಎಸ್.", "__S__"),
        ("ಎಂ.", "__M__"),
        ("ಕೆ.", "__K__"),
        ("ಬಿ.", "__B__"),
        ("ರೂ.", "__RS__"),
        ("ಕಿ.ಮೀ.", "__KM__"),
    ]
    for orig, token in abbrevs:
        protected = protected.replace(orig, token)

    # Regex split pattern for sentence terminators
    sentence_delimiters = r'([।॥!?]|\.(?=\s+|$))'
    parts = re.split(sentence_delimiters, protected)

    sentences = []
    buffer = ""
    for part in parts:
        if not part:
            continue
        if re.match(r'^[।॥!?.]+$', part):
            buffer += part
            clean = buffer.strip()
            if clean:
                # Restore abbreviations
                for orig, token in abbrevs:
                    clean = clean.replace(token, orig)
                sentences.append(clean)
            buffer = ""
        else:
            buffer += part

    if buffer.strip():
        clean = buffer.strip()
        for orig, token in abbrevs:
            clean = clean.replace(token, orig)
        sentences.append(clean)

    return sentences

def convert_kannada_digits_to_ascii(text: str) -> str:
    """Convert Kannada numerals (೦-೯) to standard ASCII digits (0-9) for number verification."""
    if not text:
        return ""
    return text.translate(KANNADA_DIGIT_MAP)

def extract_numbers_from_text(text: str) -> List[str]:
    """Extract all numbers (integers, decimals, crore, lakh, percentages) from text in normalized form."""
    if not text:
        return []
    ascii_text = convert_kannada_digits_to_ascii(text)
    # Find all standard digits with optional commas and decimals
    numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', ascii_text)
    # Strip commas for uniform comparison
    return [n.replace(',', '') for n in numbers]

