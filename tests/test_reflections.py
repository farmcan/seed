from seed.reflections import (
    ReflectionRecord,
    append_reflection_record,
    build_revision_suggestions,
    load_reflection_records,
    reflection_log_path,
    revision_suggestions_path,
    write_revision_suggestions,
)


def test_reflection_log_path(tmp_path):
    assert reflection_log_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "reflections" / "某-up.reflection.jsonl"
    )


def test_append_and_load_reflection_record(tmp_path):
    record = ReflectionRecord(
        owner="demo",
        task="write analysis",
        outcome="useful",
        worked=["clear framing"],
        failed=["weak evidence"],
        revise=["add source check"],
    )

    path = append_reflection_record(library_root=tmp_path, record=record)
    records = load_reflection_records(path)

    assert len(records) == 1
    assert records[0].owner == "demo"
    assert records[0].worked == ["clear framing"]
    assert records[0].revise == ["add source check"]


def test_revision_suggestions_path(tmp_path):
    assert revision_suggestions_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "reflections" / "某-up.revision-suggestions.md"
    )


def test_build_revision_suggestions_dedupes_observations():
    records = [
        ReflectionRecord(
            owner="demo",
            task="task 1",
            outcome="ok",
            worked=["clear framing", "clear framing"],
            failed=["weak evidence"],
            revise=["add source check"],
        )
    ]

    text = build_revision_suggestions(owner="demo", records=records)

    assert text.count("clear framing") == 1
    assert "- [ ] weak evidence" in text
    assert "- [ ] add source check" in text


def test_write_revision_suggestions(tmp_path):
    append_reflection_record(
        library_root=tmp_path,
        record=ReflectionRecord(owner="demo", task="task", outcome="ok", revise=["tighten hook"]),
    )

    path = write_revision_suggestions(library_root=tmp_path, owner="demo")

    assert "tighten hook" in path.read_text(encoding="utf-8")
