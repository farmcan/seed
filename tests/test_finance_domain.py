import json
from datetime import UTC, datetime

from seed.domains.finance import (
    build_finance_digest_artifact,
    build_market_data_record,
    enrich_finance_digest_with_prices,
    finance_digest_output_path,
    parse_stooq_daily_csv,
    write_finance_digest_artifact,
)


def test_build_finance_digest_artifact_groups_signals(tmp_path):
    first = tmp_path / "one.finance-signals.json"
    second = tmp_path / "two.finance-signals.json"
    first.write_text(
        json.dumps(
            {
                "title": "One",
                "owner": "demo",
                "platform": "bilibili",
                "stance_summary": "watching AI",
                "instruments": [{"name": "AI"}],
                "recommendations": [{"instrument": "AI", "action": "watch"}],
                "macro_theses": [{"thesis": "liquidity matters"}],
                "methodology_signals": [{"method": "event catalyst"}],
                "risk_flags": ["not financial advice"],
                "evidence_gaps": ["missing price data"],
            }
        ),
        encoding="utf-8",
    )
    second.write_text(
        json.dumps(
            {
                "title": "Two",
                "owner": "demo",
                "platform": "bilibili",
                "instruments": [{"name": "AI"}],
                "recommendations": [{"instrument": "AI", "action": "hold"}],
                "methodology_signals": [{"method": "event catalyst"}],
                "risk_flags": [],
                "evidence_gaps": [],
            }
        ),
        encoding="utf-8",
    )

    artifact = build_finance_digest_artifact(
        signal_paths=[first, second],
        owner="demo",
        published_after=datetime(2026, 5, 10, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
        video_metadata_by_title={
            "One": {"published_at": "2026-05-12T00:00:00+00:00"},
            "Two": {"published_at": "2026-05-01T00:00:00+00:00"},
        },
    )

    assert artifact["videos_analyzed"] == 1
    assert artifact["totals"]["recommendations"] == 1
    assert artifact["totals"]["viewpoint_events"] == 1
    assert artifact["instruments"][0]["name"] == "AI"
    assert artifact["instruments"][0]["mentions"] == 1
    assert artifact["methodology_signals"][0]["method"] == "event catalyst"
    assert artifact["risk_flags"] == ["not financial advice"]
    assert artifact["viewpoint_events"][0]["event_id"].startswith("one-ai-")


def test_finance_digest_output_path_and_write(tmp_path):
    path = finance_digest_output_path(
        library_root=tmp_path,
        owner="王财经",
        published_after=datetime(2026, 5, 4, tzinfo=UTC),
        published_before=datetime(2026, 5, 14, tzinfo=UTC),
    )
    write_finance_digest_artifact(path, {"kind": "finance_digest"})

    assert path == tmp_path / "distilled" / "王财经.20260504-to-20260514.finance-digest.json"
    assert json.loads(path.read_text(encoding="utf-8"))["kind"] == "finance_digest"


def test_parse_stooq_daily_csv_and_market_data_record():
    history = parse_stooq_daily_csv(
        """Date,Open,High,Low,Close,Volume
2026-05-11,10,11,9,10,100
2026-05-12,10,12,10,12,100
"""
    )
    record = build_market_data_record(
        ticker="demo.us",
        published_at=datetime(2026, 5, 12, 12, tzinfo=UTC),
        history=history,
        benchmark_ticker=None,
        benchmark_history=[],
        provider="stooq",
    )

    assert record["status"] == "priced"
    assert record["published_close"] == 12
    assert record["latest_close"] == 12
    assert record["return_pct"] == 0.0


def test_enrich_finance_digest_with_prices(monkeypatch):
    digest = {
        "kind": "finance_digest",
        "recommendations": [{"instrument": "AI", "video_title": "One"}],
        "viewpoint_events": [
            {
                "event_id": "one-ai-1",
                "instrument": "AI",
                "video_title": "One",
                "action": "watch",
            }
        ],
        "video_records": [{"title": "One", "published_at": "2026-05-11T00:00:00+00:00"}],
        "totals": {"recommendations": 1, "viewpoint_events": 1},
    }

    def fake_history(ticker):
        return [
            {"date": "2026-05-10", "close": 10.0},
            {"date": "2026-05-12", "close": 12.0},
        ]

    monkeypatch.setattr("seed.domains.finance.fetch_stooq_daily_history", fake_history)

    enriched = enrich_finance_digest_with_prices(
        digest,
        ticker_map={"AI": "demo.us", "ai": "demo.us"},
        benchmark_ticker=None,
    )

    market_data = enriched["recommendations"][0]["market_data"]
    assert enriched["kind"] == "priced_finance_digest"
    assert market_data["status"] == "priced"
    assert market_data["return_pct"] == 20.0
    assert enriched["totals"]["priced_recommendations"] == 1
    assert enriched["totals"]["priced_viewpoint_events"] == 1
    outcomes = enriched["viewpoint_events"][0]["event_outcomes"]
    assert outcomes["status"] == "priced"
    assert outcomes["horizons"]["1D"]["status"] == "priced"
    assert outcomes["horizons"]["1D"]["asset_return"] == 20.0
    assert outcomes["latest"]["status"] == "priced"
