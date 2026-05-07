from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from seed.library import init_library, save_methodology, save_source_record, slugify
from seed.models import Methodology, Platform, SourceRecord


app = typer.Typer(help="Personal content-to-methodology distillation toolkit.")
console = Console()


@app.command("init-library")
def init_library_cmd(
    root: Annotated[Path, typer.Option("--root", help="Knowledge library root.")] = Path("library"),
) -> None:
    paths = init_library(root)
    for path in paths:
        console.print(f"created {path}")


@app.command("ingest-url")
def ingest_url(
    url: Annotated[str, typer.Argument(help="Content URL to record or ingest.")],
    platform: Annotated[Platform, typer.Option("--platform")],
    owner: Annotated[str, typer.Option("--owner")],
    title: Annotated[str | None, typer.Option("--title")] = None,
    authorized: Annotated[bool, typer.Option("--authorized")] = False,
    download: Annotated[bool, typer.Option("--download/--no-download")] = False,
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    if download and not authorized:
        raise typer.BadParameter("--download requires --authorized")

    record = SourceRecord(
        url=url,
        platform=platform,
        owner=owner,
        title=title,
        authorized=authorized,
    )
    path = save_source_record(root, record)
    console.print(f"recorded source at {path}")
    if download:
        console.print("download adapter is intentionally not implemented in the seed bootstrap")


@app.command("distill-note")
def distill_note(
    note_path: Annotated[Path, typer.Argument(help="Transcript or note markdown file.")],
    owner: Annotated[str, typer.Option("--owner")],
    topic: Annotated[str, typer.Option("--topic")],
    root: Annotated[Path, typer.Option("--root")] = Path("library"),
) -> None:
    text = note_path.read_text(encoding="utf-8")
    first_lines = [line.strip("- #") for line in text.splitlines() if line.strip()][:5]
    methodology = Methodology(
        id=slugify(f"{owner}-{topic}"),
        title=f"{owner} - {topic}",
        owner=owner,
        topic=topic,
        core_ideas=first_lines,
        agent_checks=["是否有明确适用场景？", "是否能转成可执行步骤？", "是否有反例或失效条件？"],
    )
    path = save_methodology(root, methodology)
    console.print(f"created draft methodology at {path}")
