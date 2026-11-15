import workflow
from storage import get_run, list_runs


def test_under_200_words_skips_ai(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_DB_PATH", str(tmp_path / "test.db"))

    def no_ai(*args):
        raise AssertionError("AI should not run on short content")

    monkeypatch.setattr(workflow, "_call_groq", no_ai)
    result = workflow.run_agent("text", "word " * 199)
    assert result["word_count"] == 199
    assert result["status"] == "skipped_short"
    assert result["summary"] is None and result["category"] is None
    assert result["logged"] is True
    assert [e["node"] for e in result["events"]] == [
        "input", "processing", "execution_log",
    ]
    assert get_run(result["run_id"])["cleaned_content"] == result["cleaned_content"]


def test_exactly_200_words_gets_ai_and_category(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_DB_PATH", str(tmp_path / "test.db"))
    responses = iter(["A concise factual summary.", "Technology"])
    monkeypatch.setattr(workflow, "_call_groq", lambda *_: next(responses))
    result = workflow.run_agent("text", "word " * 200)
    assert result["word_count"] == 200
    assert result["status"] == "completed"
    assert result["summary"] == "A concise factual summary."
    assert result["category"] == "Technology"
    assert [e["node"] for e in result["events"]] == [
        "input", "processing", "summary", "category", "execution_log",
    ]
    assert len(list_runs()) == 1


def test_url_uses_extractor(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(
        workflow, "fetch_article",
        lambda url: ("News " * 201, "https://example.com/real-article"),
    )
    responses = iter(["Reported event and facts.", "World"])
    monkeypatch.setattr(workflow, "_call_groq", lambda *_: next(responses))
    result = workflow.run_agent("url", "https://example.com/story")
    assert result["source_url"] == "https://example.com/real-article"
    assert result["word_count"] == 201
    assert result["category"] == "World"
    assert result["logged"]


def test_empty_input_is_logged_as_error(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_DB_PATH", str(tmp_path / "test.db"))
    result = workflow.run_agent("text", "  ")
    assert result["status"] == "error"
    assert result["logged"] is True
    assert [e["node"] for e in result["events"]] == [
        "input", "processing", "execution_log",
    ]
