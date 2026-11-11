from site_assistant.ingestion.normalization import normalize_persian_text


def test_unifies_arabic_yeh_and_kaf() -> None:
    assert normalize_persian_text("يك كتاب") == "یک کتاب"


def test_converts_arabic_indic_digits_to_persian() -> None:
    assert normalize_persian_text("١٢٣") == "۱۲۳"


def test_preserves_persian_half_space() -> None:
    assert normalize_persian_text("مي شود") == "می شود"
    assert normalize_persian_text("می‌شود") == "می‌شود"


def test_collapses_repeated_spaces_and_trims() -> None:
    assert normalize_persian_text("  سلام   دنیا  ") == "سلام دنیا"
