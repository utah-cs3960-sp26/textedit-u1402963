import warnings

from editor.highlighters.detector import LanguageDetector


def test_deprecated_highlighter_map_warns_once():
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always", DeprecationWarning)

        _ = LanguageDetector.HIGHLIGHTER_MAP["python"]
        _ = LanguageDetector.HIGHLIGHTER_MAP.get("python")

    assert any(issubclass(w.category, DeprecationWarning) for w in recorded)
    assert len(recorded) == 1
