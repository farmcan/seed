from seed.domains.earnings import (
    build_earnings_distillation_prompt,
    build_sec_earnings_artifact,
    extract_financial_concepts,
    normalize_cik,
    recent_filings_from_submissions,
    sec_filing_index_url,
)


def test_recent_filings_and_sec_urls():
    submissions = {
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-26-000001", "0000320193-26-000002"],
                "form": ["10-Q", "4"],
                "filingDate": ["2026-05-01", "2026-05-02"],
                "reportDate": ["2026-03-31", ""],
                "primaryDocument": ["aapl-20260331.htm", "xslF345X05/doc.xml"],
            }
        }
    }

    filings = recent_filings_from_submissions(submissions, forms=["10-Q"], limit=5)

    assert normalize_cik("CIK320193") == "0000320193"
    assert filings == [
        {
            "accession_number": "0000320193-26-000001",
            "form": "10-Q",
            "filing_date": "2026-05-01",
            "report_date": "2026-03-31",
            "acceptance_datetime": None,
            "primary_document": "aapl-20260331.htm",
            "primary_doc_description": None,
        }
    ]
    assert sec_filing_index_url(
        cik="0000320193",
        accession_number="0000320193-26-000001",
    ).endswith("/320193/000032019326000001/0000320193-26-000001-index.html")


def test_extract_financial_concepts_and_prompt(tmp_path):
    companyfacts = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "label": "Revenues",
                    "units": {
                        "USD": [
                            {
                                "val": 100,
                                "fy": 2026,
                                "fp": "Q1",
                                "form": "10-Q",
                                "filed": "2026-05-01",
                                "end": "2026-03-31",
                                "accn": "0000320193-26-000001",
                            }
                        ]
                    },
                }
            }
        }
    }
    artifact = build_sec_earnings_artifact(
        identifier="AAPL",
        company={"cik": "0000320193", "ticker": "AAPL", "title": "Apple Inc."},
        submissions={"cik": "0000320193", "name": "Apple Inc.", "filings": {"recent": {}}},
        companyfacts=companyfacts,
    )
    path = tmp_path / "aapl.sec-earnings.json"
    path.write_text(__import__("json").dumps(artifact), encoding="utf-8")

    prompt = build_earnings_distillation_prompt(earnings_artifact_path=path)

    assert extract_financial_concepts(companyfacts)["revenue"][0]["value"] == 100
    assert artifact["kind"] == "sec_earnings"
    assert artifact["financial_facts"]["revenue"][0]["accession_number"] == "0000320193-26-000001"
    assert '"kind": "earnings_digest"' in prompt
    assert "Do not make investment recommendations" in prompt
