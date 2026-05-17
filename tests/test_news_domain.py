import json
from datetime import UTC, datetime

from seed.domains.news import (
    build_gdelt_doc_url,
    build_news_facts_prompt,
    build_news_search_artifact,
    gdelt_datetime,
    normalize_gdelt_articles,
)


def test_build_gdelt_doc_url_uses_artlist_json_and_time_window():
    url = build_gdelt_doc_url(
        query='"Trump" "China visit"',
        max_records=999,
        timespan=None,
        published_after=datetime(2026, 5, 1, tzinfo=UTC),
        published_before=datetime(2026, 5, 2, tzinfo=UTC),
    )

    assert "mode=artlist" in url
    assert "format=json" in url
    assert "maxrecords=250" in url
    assert "startdatetime=20260501000000" in url
    assert "enddatetime=20260502000000" in url
    assert gdelt_datetime(datetime(2026, 5, 1, 1, tzinfo=UTC)) == "20260501010000"


def test_build_news_search_artifact_and_prompt(tmp_path):
    articles = normalize_gdelt_articles(
        [
            {
                "title": "Demo headline",
                "url": "https://example.com/a",
                "domain": "example.com",
                "language": "English",
                "sourcecountry": "US",
                "seendate": "20260501T120000Z",
            }
        ]
    )
    artifact = build_news_search_artifact(
        query="demo",
        articles=articles,
        source_url="https://api.gdeltproject.org/demo",
    )
    path = tmp_path / "demo.news-search.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    prompt = build_news_facts_prompt(news_artifact_path=path, topic="demo")

    assert artifact["kind"] == "news_search"
    assert artifact["article_count"] == 1
    assert artifact["articles"][0]["provider"] == "gdelt-doc-2.0"
    assert '"kind": "news_facts_digest"' in prompt
    assert "facts, reported claims, uncertainty" in prompt
