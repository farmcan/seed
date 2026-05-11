from seed.semantics.validation import (
    creator_profile_validation_output_path,
    validate_creator_profile,
    write_creator_profile_validation,
)


def test_creator_profile_validation_output_path(tmp_path):
    assert creator_profile_validation_output_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "distilled" / "某-up.creator-profile.validation.json"
    )


def test_validate_creator_profile_warns_on_uncited_strong_claim(tmp_path):
    profile = tmp_path / "demo.creator-profile.md"
    profile.write_text(
        """# Creator Profile

## Creator Summary

- This creator always turns geopolitical stories into a repeatable decision framework.
- This single-video pattern is provisional.
- This claim is grounded by transcript evidence. [T1]
""",
        encoding="utf-8",
    )

    report = validate_creator_profile(profile, owner="demo")

    assert report["status"] == "warnings"
    assert len(report["findings"]) == 1
    assert report["findings"][0]["section"] == "Creator Summary"


def test_write_creator_profile_validation(tmp_path):
    path = write_creator_profile_validation(tmp_path / "validation.json", {"findings": []})

    assert path.read_text(encoding="utf-8") == '{\n  "findings": []\n}'
