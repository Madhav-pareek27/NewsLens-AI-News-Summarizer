from storage import get_run, get_run_stats, list_runs, save_run


def test_storage_stats(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWS_DB_PATH", str(tmp_path / "stats.db"))
    for idx, status in enumerate(["completed", "skipped_short", "completed", "error"]):
        save_run({
            "run_id": f"test-{idx}", "created_at": f"2026-11-14T00:00:0{idx}+00:00",
            "input_type": "text", "source_url": None,
            "status": status, "word_count": idx * 100,
            "category": None, "summary": None, "events": [],
        })
    stats = get_run_stats()
    assert stats["total"] == 4
    assert stats["completed"] == 2
    assert stats["skipped_short"] == 1
    assert len(list_runs()) == 4
    assert get_run("test-0")["status"] == "completed"
