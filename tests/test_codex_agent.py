from seed.agents.codex import build_codex_exec_command, run_codex_prompt


def test_run_codex_prompt_dry_run_writes_prompt(tmp_path):
    output = tmp_path / "prompt.md"

    run_codex_prompt(prompt="hello", output_path=output, dry_run=True)

    assert output.read_text(encoding="utf-8") == "hello"


def test_build_codex_exec_command_matches_current_cli(tmp_path):
    output = tmp_path / "summary.md"

    command = build_codex_exec_command(output_path=output, cwd=tmp_path, model="gpt-5.4-mini")

    assert command[:4] == ["codex", "exec", "--model", "gpt-5.4-mini"]
    assert "--ask-for-approval" not in command
    assert "--output-last-message" in command
    assert command[-1] == "-"
