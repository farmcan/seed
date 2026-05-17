from seed.reports.finance_news import (
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
