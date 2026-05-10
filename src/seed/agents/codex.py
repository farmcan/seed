from __future__ import annotations

import subprocess
from pathlib import Path


def run_codex_prompt(
    *,
    prompt: str,
    output_path: Path,
    model: str | None = None,
    cwd: Path | None = None,
    dry_run: bool = False,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        output_path.write_text(prompt, encoding="utf-8")
        return output_path

    command = build_codex_exec_command(
        output_path=output_path,
        model=model,
        cwd=cwd or Path.cwd(),
    )
    subprocess.run(command, input=prompt, text=True, check=True)
    return output_path


def build_codex_exec_command(
    *,
    output_path: Path,
    cwd: Path,
    model: str | None = None,
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--cd",
        str(cwd or Path.cwd()),
        "--sandbox",
        "read-only",
        "--output-last-message",
        str(output_path),
        "-",
    ]
    if model:
        command[2:2] = ["--model", model]

    return command
