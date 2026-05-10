from seed.reflections import (
    ReflectionRecord,
    append_reflection_record,
    load_reflection_records,
    reflection_log_path,
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
