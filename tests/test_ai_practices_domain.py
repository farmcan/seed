import json
from datetime import UTC, datetime

from seed.domains.ai_practices import (
    ai_practice_digest_output_path,
    build_ai_practice_digest_artifact,
    write_ai_practice_digest_artifact,
)


def test_build_ai_practice_digest_artifact_groups_signals(tmp_path):
    first = tmp_path / "one.ai-practice-signals.json"
    second = tmp_path / "two.ai-practice-signals.json"
    first.write_text(
        json.dumps(
            {
                "title": "One",
                "person": "demo",
                "owner": "demo",
                "platform": "youtube",
                "ai_usage_summary": "Uses agents for code review.",
                "practice_events": [{"practice": "agent code review", "tools": ["Codex"]}],
                "belief_events": [{"claim": "AI changes software iteration."}],
                "capability_signals": [{"capability": "evals", "why_it_matters": "trust"}],
                "tooling_patterns": [{"tool_or_pattern": "agent workspace", "use_case": "coding"}],
                "personal_application_candidates": [{"candidate": "daily agent review"}],
                "project_application_candidates": [{"candidate": "add eval artifact"}],
                "evidence_gaps": ["missing demo"],
                "open_questions": ["Which evals?"],
            }
        ),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "title": "Two",
                "person": "demo",
                "platform": "youtube",
                "practice_events": [{"practice": "paper reading"}],
                "capability_signals": [{"capability": "evals"}],
                "tooling_patterns": [{"tool_or_pattern": "notebook"}],
            }
        ),
        encoding="utf-8",
    )

    artifact = build_ai_practice_digest_artifact(
        signal_paths=[first, second],
        person="demo",
        published_after=datetime(2026, 5, 10, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
        video_metadata_by_title={
            "One": {"published_at": "2026-05-12T00:00:00+00:00"},
            "Two": {"published_at": "2026-05-01T00:00:00+00:00"},
        },
    )

    assert artifact["videos_analyzed"] == 1
    assert artifact["totals"]["practice_events"] == 1
    assert artifact["totals"]["belief_events"] == 1
    assert artifact["totals"]["capability_signals"] == 1
    assert artifact["capability_signals"][0]["capability"] == "evals"
    assert artifact["practice_events"][0]["video_title"] == "One"
    assert artifact["evidence_gaps"] == ["missing demo"]
    assert artifact["open_questions"] == ["Which evals?"]


def test_ai_practice_digest_output_path_and_write(tmp_path):
    path = ai_practice_digest_output_path(
        library_root=tmp_path,
        person="某 AI 人",
        published_after=datetime(2026, 5, 4, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
    )
    write_ai_practice_digest_artifact(path, {"kind": "ai_practice_digest"})

    assert path == tmp_path / "distilled" / "某-ai-人.20260504-to-20260514.ai-practice-digest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["kind"] == "ai_practice_digest"
