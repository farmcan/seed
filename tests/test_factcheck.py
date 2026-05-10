import json

from seed.factcheck import build_claims_artifact, claims_output_path, write_claims_artifact


def test_claims_output_path_uses_title(tmp_path):
    path = claims_output_path(library_root=tmp_path, title="法德 欧洲")

    assert path == tmp_path / "claims" / "法德-欧洲.claims.json"


def test_build_claims_artifact_from_semantics(tmp_path):
    semantics = tmp_path / "demo.video-semantics.md"
    semantics.write_text(
        """## Metadata

- Title: Demo

## Verbal Language

- Main claims:
  - Claim A.
  - Claim B.
- Explanation style: direct.

## Open Questions

- Need source C.
""",
        encoding="utf-8",
    )

    artifact = build_claims_artifact(semantics_path=semantics)

    assert artifact["title"] == "Demo"
    assert [claim["id"] for claim in artifact["claims"]] == [
        "claim-001",
        "claim-002",
        "claim-003",
    ]
    assert artifact["claims"][0]["text"] == "Claim A."
    assert artifact["claims"][0]["status"] == "unverified"
    assert artifact["claims"][2]["source_section"] == "Open Questions"


def test_write_claims_artifact(tmp_path):
    path = tmp_path / "demo.claims.json"

    write_claims_artifact(path, {"title": "Demo", "claims": []})

    assert json.loads(path.read_text(encoding="utf-8"))["title"] == "Demo"
