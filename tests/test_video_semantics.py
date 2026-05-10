from seed.semantics.analyzer import (
    build_video_semantics_prompt,
    run_video_semantics_analysis,
    video_semantics_output_path,
)


def test_video_semantics_output_path_uses_title(tmp_path):
    path = video_semantics_output_path(
        library_root=tmp_path,
        transcript_path=tmp_path / "demo.transcript.md",
        title="视频 语义",
    )

    assert path == tmp_path / "semantics" / "视频-语义.video-semantics.md"


def test_build_video_semantics_prompt_includes_transcript_and_visual_notes(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    visual = tmp_path / "demo.visual.md"
    skill = tmp_path / "SKILL.md"
    transcript.write_text("---\ntitle: Demo\n---\n\nspoken content", encoding="utf-8")
    visual.write_text("---\ntitle: Visual\n---\n\n# Visual Notes\n\nscene evidence", encoding="utf-8")
    skill.write_text("Analyze semantics.", encoding="utf-8")

    prompt = build_video_semantics_prompt(
        transcript_path=transcript,
        visual_notes_path=visual,
        skill_path=skill,
        title="Demo",
        owner="creator",
        platform="xiaohongshu",
    )

    assert "Analyze semantics." in prompt
    assert "spoken content" in prompt
    assert "<visual_notes" in prompt
    assert "scene evidence" in prompt
    assert "Owner: creator" in prompt


def test_run_video_semantics_analysis_dry_run_writes_prompt(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    skill = tmp_path / "SKILL.md"
    output = tmp_path / "demo.prompt.md"
    transcript.write_text("spoken content", encoding="utf-8")
    skill.write_text("Analyze semantics.", encoding="utf-8")

    run_video_semantics_analysis(
        transcript_path=transcript,
        output_path=output,
        skill_path=skill,
        dry_run=True,
    )

    assert output.exists()
    assert "spoken content" in output.read_text(encoding="utf-8")
