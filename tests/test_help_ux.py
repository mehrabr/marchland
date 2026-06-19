"""Tests for UX-11: unknown-topic error wraps cleanly on narrow terminals."""
from clients.cli.help import get_help


def test_ux11_unknown_topic_error_is_multiline():
    """Error for unknown topic must put the topic list on a separate line."""
    text = get_help('nonexistent')
    lines = text.splitlines()
    error_line = next((l for l in lines if 'unknown' in l.lower()), '')
    topic_on_error_line_count = sum(
        1 for t in ('march', 'battle', 'siege', 'stations', 'receipts', 'dispatch', 'trace', 'table')
        if t in error_line.lower()
    )
    assert topic_on_error_line_count < 4, (
        f"Available topics must not all be on the error line; got: {error_line!r}"
    )


def test_ux11_unknown_topic_lists_all_topics_in_output():
    """Error output must still list all available topics."""
    text = get_help('nonexistent').lower()
    for topic in ('march', 'battle', 'siege'):
        assert topic in text, f"Topic '{topic}' must appear in unknown-topic error"


def test_ux11_unknown_topic_topics_on_own_lines():
    """Each topic must appear on its own line in the error output."""
    text = get_help('nonexistent')
    lines = text.splitlines()
    # At least 3 topic names must each appear alone on a line (possibly with leading spaces)
    topic_solo_lines = [l.strip() for l in lines if l.strip() in
                        ('march', 'battle', 'siege', 'stations', 'receipts', 'dispatch', 'trace', 'table')]
    assert len(topic_solo_lines) >= 3, (
        f"At least 3 topics must appear on their own lines; got solo lines: {topic_solo_lines}"
    )
