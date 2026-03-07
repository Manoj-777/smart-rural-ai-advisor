import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import translate_helper


def test_non_span_html_tags_are_removed():
    text = "Soil advice: <div><b>Use compost</b></div> <i>weekly</i>."

    cleaned = translate_helper._strip_html_artifacts(text)

    assert '<div>' not in cleaned
    assert '</div>' not in cleaned
    assert '<b>' not in cleaned
    assert '</b>' not in cleaned
    assert '<i>' not in cleaned
    assert '</i>' not in cleaned
    assert 'Use compost' in cleaned
    assert 'weekly' in cleaned


def test_markdown_content_is_preserved_when_no_html_present():
    text = "**NPK plan**\n- Apply 20kg/acre\n- Irrigate lightly"

    cleaned = translate_helper._strip_html_artifacts(text)

    assert cleaned == text
