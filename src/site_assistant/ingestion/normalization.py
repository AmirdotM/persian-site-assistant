"""Persian text normalization."""

import re
import unicodedata

_ARABIC_TO_PERSIAN = str.maketrans(
    {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
        "ة": "ه",
        "ـ": "",
    }
)
_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩", "۰۱۲۳۴۵۶۷۸۹")


def normalize_persian_text(text: str) -> str:
    """Normalize Persian characters and whitespace."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.translate(_ARABIC_TO_PERSIAN)
    normalized = normalized.translate(_DIGIT_TRANSLATION)
    normalized = re.sub(r"[ \t\u00a0]+", " ", normalized)
    normalized = re.sub(r" *\n *", "\n", normalized)
    return normalized.strip()
