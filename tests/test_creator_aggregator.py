from seed.semantics.aggregator import (
    build_creator_profile_prompt,
    creator_profile_output_path,
    find_video_semantics_files,
    run_creator_profile_aggregation,
    semantics_matches_owner,
)


def test_creator_profile_output_path(tmp_path):
    assert creator_profile_output_path(library_root=tmp_path, owner="某 UP") == (
        tmp_path / "distilled" / "某-up.creator-profile.md"
    )


def test_semantics_matches_owner_from_metadata_line():
    assert semantics_matches_owner("- Owner: Demo UP\ncontent", "demo up")
    assert semantics_matches_owner("Owner: 某UP\ncontent", "某UP")
    assert not semantics_matches_owner("- Owner: other\ncontent", "demo up")


def test_find_video_semantics_files_filters_by_owner(tmp_path):
    semantics_dir = tmp_path / "semantics"
    semantics_dir.mkdir()
    match = semantics_dir / "a.video-semantics.md"
    miss = semantics_dir / "b.video-semantics.md"
    match.write_text("## Metadata\n\n- Owner: demo\n\ncontent", encoding="utf-8")
    miss.write_text("## Metadata\n\n- Owner: other\n\ncontent", encoding="utf-8")

    assert find_video_semantics_files(library_root=tmp_path, owner="demo") == [match]


def test_build_creator_profile_prompt_includes_all_semantics(tmp_path):
    skill = tmp_path / "SKILL.md"
    first = tmp_path / "first.video-semantics.md"
    second = tmp_path / "second.video-semantics.md"
    skill.write_text("Aggregate creator profile.", encoding="utf-8")
    first.write_text("- Owner: demo\nfirst method", encoding="utf-8")
    second.write_text("- Owner: demo\nsecond method", encoding="utf-8")

    prompt = build_creator_profile_prompt(
        semantics_paths=[first, second],
        skill_path=skill,
        owner="demo",
        platform="bilibili",
    )

    assert "Aggregate creator profile." in prompt
    assert "Video semantics count: 2" in prompt
    assert "first method" in prompt
    assert "second method" in prompt


def test_run_creator_profile_aggregation_dry_run_writes_prompt(tmp_path):
    skill = tmp_path / "SKILL.md"
    semantics = tmp_path / "demo.video-semantics.md"
    output = tmp_path / "demo.creator-profile.prompt.md"
    skill.write_text("Aggregate creator profile.", encoding="utf-8")
    semantics.write_text("- Owner: demo\nmethod", encoding="utf-8")

    run_creator_profile_aggregation(
        semantics_paths=[semantics],
        output_path=output,
        skill_path=skill,
        owner="demo",
        dry_run=True,
    )

    assert output.exists()
    assert "method" in output.read_text(encoding="utf-8")
