import json

from seed.costs import build_cost_ledger, cost_ledger_output_path, reserved_cost_item


def test_cost_ledger_output_path(tmp_path):
    assert cost_ledger_output_path(library_root=tmp_path, title="Demo 视频") == (
        tmp_path / "costs" / "demo-视频.ledger.json"
    )


def test_build_cost_ledger_sums_reports_and_keeps_reserved_items(tmp_path):
    report = tmp_path / "demo.cost.json"
    report.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "kind": "qwen_vl",
                        "estimated_cost": {"amount": 0.25, "currency": "USD"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    ledger = build_cost_ledger(
        title="Demo",
        cost_report_paths=[report],
        reserved_items=[
            reserved_cost_item(kind="codex", provider="codex", operation="analyze-video-semantics")
        ],
    )

    assert ledger["kind"] == "cost_ledger"
    assert ledger["totals"] == {"USD": 0.25}
    assert ledger["items"][0]["source_report_path"] == str(report)
    assert ledger["items"][1]["status"] == "reserved"
