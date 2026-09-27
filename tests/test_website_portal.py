from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).parents[1]
HTML = ROOT / "website" / "index.html"


def main():
    source = HTML.read_text(encoding="utf-8")
    assert "<!doctype html>" in source.lower()
    assert "<style>" in source
    assert "<script>" in source
    assert "localStorage.getItem(KEY)" in source
    assert "localStorage.setItem(KEY" in source
    for marker in (
        "view-dashboard", "view-twin", "view-cycle", "view-trends",
        "view-healing", "view-complications", "view-reports",
        "view-local", "view-settings",
    ):
        assert marker in source, marker
    for prohibited in (
        "Live Sensor Data", "Wearable Connected", "PPG", "GSR", "IMU",
        "$CP3", "GPIO",
    ):
        assert prohibited not in source, prohibited
    assert "fetch(" not in source
    assert "new WebSocket" not in source
    assert "XMLHttpRequest" not in source

    class Parser(HTMLParser):
        pass

    Parser().feed(source)
    print("Patient web portal validation: PASS")


if __name__ == "__main__":
    main()
