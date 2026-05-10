from seed.summarizers.codex_runner import (
    build_codex_exec_command,
    build_summary_prompt,
    run_codex_summary,
)


def test_build_summary_prompt_includes_skill_and_transcript(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    skill = tmp_path / "SKILL.md"
    transcript.write_text("---\ntitle: Demo\n---\n\nhello transcript", encoding="utf-8")
    skill.write_text("Summarize with sections.", encoding="utf-8")

    prompt = build_summary_prompt(
        transcript_path=transcript,
        skill_path=skill,
        title="Demo",
        owner="owner",
        platform="bilibili",
    )

    assert "Summarize with sections." in prompt
    assert "hello transcript" in prompt
    assert "Platform: bilibili" in prompt


def test_build_summary_prompt_includes_visual_notes(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    skill = tmp_path / "SKILL.md"
    visual = tmp_path / "demo.visual.md"
    transcript.write_text("spoken words", encoding="utf-8")
    skill.write_text("Summarize with sections.", encoding="utf-8")
    visual.write_text("---\ntitle: Visual\n---\n\n# Visual Notes\n\nscene changes", encoding="utf-8")

    prompt = build_summary_prompt(
        transcript_path=transcript,
        skill_path=skill,
        visual_notes_path=visual,
    )

    assert "<visual_notes" in prompt
    assert "scene changes" in prompt


def test_run_codex_summary_dry_run_writes_prompt(tmp_path):
    transcript = tmp_path / "demo.transcript.md"
    skill = tmp_path / "SKILL.md"
    output = tmp_path / "summary.prompt.md"
    transcript.write_text("hello transcript", encoding="utf-8")
    skill.write_text("Summarize with sections.", encoding="utf-8")

    run_codex_summary(
        transcript_path=transcript,
        output_path=output,
        skill_path=skill,
        dry_run=True,
    )

    assert output.exists()
    assert "hello transcript" in output.read_text(encoding="utf-8")


def test_build_codex_exec_command_matches_current_cli(tmp_path):
    output = tmp_path / "summary.md"

    command = build_codex_exec_command(output_path=output, cwd=tmp_path, model="gpt-5.4-mini")

    assert command[:4] == ["codex", "exec", "--model", "gpt-5.4-mini"]
    assert "--ask-for-approval" not in command
    assert "--output-last-message" in command
    assert command[-1] == "-"
