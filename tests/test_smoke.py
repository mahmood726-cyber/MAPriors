from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_app_html_exists_and_names_tool():
    html_path = ROOT / "map-priors.html"
    text = html_path.read_text(encoding="utf-8")

    assert html_path.exists()
    assert "MAP" in text
    assert "prior" in text.lower()


def test_e156_submission_page_exists():
    html_path = ROOT / "e156-submission" / "index.html"
    text = html_path.read_text(encoding="utf-8")

    assert html_path.exists()
    assert "E156" in text or "paper" in text.lower()
