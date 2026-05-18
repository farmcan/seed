import json

from seed.cli import build_up_homepage
from seed.reports.finance_news import (
    build_finance_news_outputs_for_owner,
    build_finance_news_report_html,
    finance_news_report_output_path,
)


def test_build_finance_news_report_html(tmp_path):
    digest_path = tmp_path / "demo.finance-digest.news-context.json"
    digest = {
        "kind": "finance_digest_with_news_context",
        "owner": "demo-up",
        "platform": "bilibili",
        "videos_analyzed": 1,
        "totals": {"news_context_matches": 1},
        "viewpoint_events": [
            {
                "event_id": "one-ai-1",
                "video_title": "AI mainline",
                "published_at": "2026-05-18T00:00:00+00:00",
                "instrument": "AI",
                "action": "watch",
                "direction": "bullish",
                "horizon": "medium",
                "conviction": "medium",
                "entry_condition": "Watch AI capex confirmation.",
                "risk_flags": ["valuation"],
                "evidence_refs": ["T1"],
                "news_context": [
                    {
                        "topic": "AI supply chain",
                        "matched_terms": ["AI"],
                        "match_score": 7,
                        "facts": [
                            {
                                "fact_id": "f1",
                                "statement": "Cloud capex remained strong.",
                                "status": "reported",
                            }
                        ],
                        "industry_impacts": [
                            {
                                "industry": "AI",
                                "mechanism": "Capex demand can affect suppliers.",
                                "possible_direction": "mixed",
                            }
                        ],
                        "market_relevance": [
                            {
                                "asset_or_sector": "AI",
                                "relevance": "Relevant to hardware equities.",
                                "fact_refs": ["f1"],
                            }
                        ],
                        "source_urls": ["https://example.test/ai"],
                    }
                ],
            }
        ],
    }

    html = build_finance_news_report_html(digest, digest_path=digest_path)

    assert "demo-up 财经观点新闻事实报告" in html
    assert "AI mainline" in html
    assert "Cloud capex remained strong." in html
    assert "Capex demand can affect suppliers." in html
    assert "https://example.test/ai" in html
    assert finance_news_report_output_path(
        library_root=tmp_path,
        digest_path=digest_path,
    ) == tmp_path / "reports" / "demo.finance-news-report.html"


def test_build_finance_news_outputs_for_owner_enriches_and_renders(tmp_path):
    root = tmp_path / "library"
    digest_path = root / "distilled" / "demo.finance-digest.json"
    news_digest_path = root / "distilled" / "ai.news-digest.json"
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps(
            {
                "kind": "finance_digest",
                "owner": "demo",
                "platform": "bilibili",
                "viewpoint_events": [
                    {
                        "event_id": "one-ai-1",
                        "instrument": "AI",
                        "ticker": "NVDA.US",
                        "video_title": "AI mainline",
                        "action": "watch",
                    }
                ],
                "totals": {"viewpoint_events": 1},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    news_digest_path.write_text(
        json.dumps(
            {
                "kind": "news_facts_digest",
                "topic": "AI capex",
                "facts": [
                    {
                        "fact_id": "f1",
                        "statement": "AI capex stayed high.",
                        "status": "reported",
                        "entities": ["AI", "Nvidia"],
                        "source_urls": ["https://example.test/ai"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    paths = build_finance_news_outputs_for_owner(
        library_root=root,
        owner="demo",
        news_digest_paths=[news_digest_path],
    )

    enriched_path = root / "distilled" / "demo.finance-digest.news-context.json"
    report_path = root / "reports" / "demo.finance-news-report.html"
    assert paths == [enriched_path, report_path]
    assert "AI capex stayed high." in report_path.read_text(encoding="utf-8")


def test_up_homepage_links_finance_news_artifacts(tmp_path):
    root = tmp_path / "library"
    owner = "demo"
    (root / "runs").mkdir(parents=True)
    (root / "distilled").mkdir(parents=True)
    (root / "reports").mkdir(parents=True)
    (root / "runs" / "demo.creator-pipeline.yaml").write_text(
        "owner: demo\nvideo_runs: []\ncreator_steps: []\n",
        encoding="utf-8",
    )
    (root / "distilled" / "demo.creator-profile.md").write_text(
        "## Creator Summary\n\nDemo profile.",
        encoding="utf-8",
    )
    (root / "distilled" / "demo.finance-digest.news-context.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (root / "reports" / "demo.finance-news-report.html").write_text(
        "<html>report</html>",
        encoding="utf-8",
    )

    homepage_path = build_up_homepage(owner=owner, root=root)
    html = homepage_path.read_text(encoding="utf-8")

    assert "demo.finance-digest.news-context.json" in html
    assert "demo.finance-news-report.html" in html
