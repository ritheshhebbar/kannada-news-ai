from typing import List, Dict, Any, Tuple
from services.ml.kannada_text import extract_numbers_from_text

def verify_sentence_numbers(source_kn: str, translated_en: str) -> Tuple[bool, List[Dict[str, Any]]]:
    """Compare normalized numbers between Kannada source sentence and English translation.
    
    Returns (passed, list_of_flags).
    """
    kn_nums = set(extract_numbers_from_text(source_kn))
    en_nums = set(extract_numbers_from_text(translated_en))

    flags = []
    # Check if numbers present in source are missing in translation
    missing_in_en = kn_nums - en_nums
    invented_in_en = en_nums - kn_nums

    if missing_in_en:
        flags.append({
            "type": "number_mismatch",
            "detail": f"Source number(s) {list(missing_in_en)} missing from translation.",
            "severity": "warning"
        })

    if invented_in_en:
        flags.append({
            "type": "number_hallucination",
            "detail": f"Number(s) {list(invented_in_en)} appeared in translation but not in source.",
            "severity": "critical"
        })

    passed = len(flags) == 0
    return passed, flags
