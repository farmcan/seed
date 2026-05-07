from pathlib import Path

from seed.transcripts import read_transcript_text, transcript_output_path, write_transcript_markdown


def test_transcript_output_path_uses_title(tmp_path):
    path = transcript_output_path(
        library_root=tmp_path,
        media_path=Path("raw/demo.mp4"),
        title="增长 方法论",
    )

    assert path == tmp_path / "transcripts" / "增长-方法论.transcript.md"


def test_write_and_read_transcript_markdown(tmp_path):
    path = tmp_path / "transcript.md"

    write_transcript_markdown(
        path,
        text="hello transcript",
        media_path=Path("raw/demo.mp4"),
        audio_path=Path("raw/demo.m4a"),
        provider="openai",
        model="gpt-4o-mini-transcribe",
        title="Demo",
        language="zh",
    )

    content = path.read_text(encoding="utf-8")
    assert "asr_provider: openai" in content
    assert read_transcript_text(path) == "# Transcript\n\nhello transcript"
