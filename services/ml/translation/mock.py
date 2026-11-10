from typing import List
from services.ml.translation.base import BaseTranslator
from services.ml.kannada_text import convert_kannada_digits_to_ascii

# Standard glossary of Karnataka entities and terms
GLOSSARY = {
    "ಬೆಂಗಳೂರು": "Bengaluru",
    "ಮೈಸೂರು": "Mysuru",
    "ಕರ್ನಾಟಕ": "Karnataka",
    "ಸಚಿವ ಸಂಪುಟ": "Cabinet",
    "ಮುಖ್ಯಮಂತ್ರಿ": "Chief Minister",
    "ಸಿದ್ದರಾಮಯ್ಯ": "Siddaramaiah",
    "ಇಸ್ರೋ": "ISRO",
    "ಉಪಗ್ರಹ": "Satellite",
    "ರಣಜಿ ಟ್ರೋಫಿ": "Ranji Trophy",
    "ಎಂ. ಚಿನ್ನಸ್ವಾಮಿ ಕ್ರೀಡಾಂಗಣ": "M. Chinnaswamy Stadium",
    "ತಮಿಳುನಾಡು": "Tamil Nadu",
    "ಮಯಾಂಕ್ ಅಗರ್ವಾಲ್": "Mayank Agarwal",
    "ಪ್ರಸಿದ್ಧ ಕೃಷ್ಣ": "Prasidh Krishna",
    "ಶ್ರೀಹರಿಕೋಟಾ": "Sriharikota",
    "ಸತೀಶ್ ಧವನ್": "Satish Dhawan",
    "ಹವಾಮಾನ": "Weather / Meteorological",
    "ಮಂತ್ರಿ": "Minister",
    "ಅಧ್ಯಕ್ಷ": "Chairman",
    "ಯೋಜನೆ": "Project",
    "ಅನುದಾನ": "Grant / Funding",
}

# Pre-computed high fidelity translations for demo articles
EXACT_CACHE = {
    "ಬೆಂಗಳೂರು ಉಪನಗರ ರೈಲು ಯೋಜನೆಗೆ ₹1,500 ಕೋಟಿ ಅನುದಾನ: ಸಚಿವ ಸಂಪುಟ ಅನುಮೋದನೆ":
        "Karnataka Cabinet Approves ₹1,500 Crore Funding for Bengaluru Suburban Rail Project",
    "ಇಸ್ರೋದಿಂದ ನೂತನ ಹವಾಮಾನ ಉಪಗ್ರಹ ಯಶಸ್ವಿ ಉಡಾವಣೆ: ಕರಾವಳಿ ಮುನ್ಸೂಚನೆಗೆ ಬಲ":
        "ISRO Successfully Launches New Meteorological Satellite to Strengthen Coastal Forecasting",
    "ರಣಜಿ ಟ್ರೋಫಿ: ಕರ್ನಾಟಕ ತಂಡಕ್ಕೆ ತಮಿಳುನಾಡು ವಿರುದ್ಧ 8 ವಿಕೆಟ್‌ಗಳ ಭರ್ಜರಿ ಜಯ":
        "Ranji Trophy: Karnataka Clinches Decisive 8-Wicket Win Against Tamil Nadu",
}

class MockTranslator(BaseTranslator):
    """High-quality offline Mock Translator for testing and local zero-GPU development."""

    def translate_headline(self, headline: str) -> str:
        clean = headline.strip()
        if clean in EXACT_CACHE:
            return EXACT_CACHE[clean]
        
        # Fallback keyword-driven translation
        result = clean
        for kn, en in GLOSSARY.items():
            result = result.replace(kn, en)
        result = convert_kannada_digits_to_ascii(result)
        return f"News: {result}"

    def translate_sentences(self, sentences: List[str]) -> List[str]:
        translated = []
        for s in sentences:
            clean = s.strip()
            if clean in EXACT_CACHE:
                translated.append(EXACT_CACHE[clean])
                continue

            # Look up glossary items and preserve numbers
            res = clean
            for kn, en in GLOSSARY.items():
                res = res.replace(kn, en)
            res = convert_kannada_digits_to_ascii(res)
            
            # Simple contextual fallback for demo phrases
            if "ಬೆಂಗಳೂರು:" in clean and "ಉಪನಗರ" in clean:
                translated.append("Bengaluru: The Karnataka Cabinet approved ₹1,500 crore in funding for the Suburban Rail Project.")
            elif "ಮುಖ್ಯಮಂತ್ರಿ" in clean:
                translated.append("The decision was taken in a cabinet meeting presided over by the Chief Minister.")
            elif "ಇಸ್ರೋ" in clean:
                translated.append("ISRO successfully launched the new meteorological satellite into orbit from the space centre.")
            elif "ರಣಜಿ ಟ್ರೋಫಿ" in clean:
                translated.append("Karnataka recorded a convincing victory in the Ranji Trophy match.")
            else:
                translated.append(f"Translation: {res}")
        return translated

