import json

from seed.claim_verification import (
    build_verified_claims_artifact,
    extract_html_title,
    verified_claims_output_path,
    write_verified_claims_artifact,
)


def test_verified_claims_output_path(tmp_path):
    path = verified_claims_output_path(
        library_root=tmp_path,
        claims_path=tmp_path / "claims" / "Demo.claims.json",
    )

    assert path == tmp_path / "claims" / "demo.verified.json"


def test_build_verified_claims_artifact_records_sources_without_fetch(tmp_path):
    claims_path = tmp_path / "demo.claims.json"
    claims_path.write_text(
        json.dumps(
            {
                "title": "Demo",
                "claims": [
                    {
                        "id": "claim-001",
                        "text": "Claim A.",
                        "status": "unverified",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    artifact = build_verified_claims_artifact(
        claims_path=claims_path,
        evidence_urls=["https://example.com/source"],
        fetch_sources=False,
    )

    assert artifact["claims"][0]["status"] == "unclear"
    assert artifact["verification_method"] == "staged-source-heuristic"
    assert "query_plan" in artifact["stages"]
    assert "evidence_snippets" in artifact["stages"]
    assert artifact["claims"][0]["verification"]["sources"] == ["https://example.com/source"]
    assert artifact["sources"][0]["fetch_status"] == "not_fetched"


def test_build_verified_claims_artifact_without_sources_stays_unverified(tmp_path):
    claims_path = tmp_path / "demo.claims.json"
    claims_path.write_text(json.dumps({"claims": [{"text": "Claim A."}]}), encoding="utf-8")

    artifact = build_verified_claims_artifact(claims_path=claims_path)

    assert artifact["claims"][0]["status"] == "unverified"


def test_build_verified_claims_artifact_can_mark_supported_with_matching_source(tmp_path, monkeypatch):
    claims_path = tmp_path / "demo.claims.json"
    claims_path.write_text(
        json.dumps({"claims": [{"id": "claim-001", "text": "France leads FCAS technology."}]}),
        encoding="utf-8",
    )

    def fake_fetch(url):
        return {
            "url": url,
            "accessed_at": "2026-05-11T00:00:00+00:00",
            "content_type": "text/html",
            "title": "FCAS source",
            "summary": "France leads FCAS technology. The programme includes German and Spanish partners.",
            "fetch_status": "ok",
        }

    monkeypatch.setattr("seed.claim_verification.fetch_evidence_source", fake_fetch)

    artifact = build_verified_claims_artifact(
        claims_path=claims_path,
        evidence_urls=["https://example.com/fcas"],
    )

    assert artifact["claims"][0]["status"] == "supported"
    assert artifact["stages"]["evidence_snippets"][0]["exact_match"] is True


def test_write_verified_claims_artifact(tmp_path):
    path = write_verified_claims_artifact(tmp_path / "verified.json", {"claims": []})

    assert json.loads(path.read_text(encoding="utf-8")) == {"claims": []}


def test_extract_html_title():
    assert extract_html_title("<html><title> Demo Source </title></html>") == "Demo Source"
