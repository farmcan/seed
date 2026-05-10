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


def test_write_transcript_markdown_can_include_chunks(tmp_path):
    path = tmp_path / "transcript.md"

    write_transcript_markdown(
        path,
        text="## Chunk 1 (00:00:00)\n\nhello",
        media_path=Path("raw/demo.mp4"),
        audio_path=Path("raw/demo.asr.mp3"),
        provider="dashscope",
        model="qwen3-asr-flash",
        chunks=[
            {
                "index": 0,
                "start_seconds": 0,
                "audio_path": "raw/demo.asr.chunks/chunk-000.mp3",
                "text_length": 5,
            }
        ],
    )

    content = path.read_text(encoding="utf-8")
    assert "asr_chunks:" in content
    assert "chunk-000.mp3" in content
    assert "## Chunk 1 (00:00:00)" in content
