from pathlib import Path

from seed.vision.notes import (
    read_visual_notes_text,
    visual_notes_output_path,
    write_visual_notes_markdown,
)


def test_visual_notes_output_path_uses_title(tmp_path):
    path = visual_notes_output_path(
        library_root=tmp_path,
        source_path=Path("frames/demo-video"),
        title="视觉 分析",
    )

    assert path == tmp_path / "notes" / "视觉-分析.visual.md"


def test_write_and_read_visual_notes_markdown(tmp_path):
    path = tmp_path / "visual.md"

    write_visual_notes_markdown(
        path,
        analysis="visible text and scenes",
        frame_dir=Path("library/frames/demo"),
        frame_paths=[Path("library/frames/demo/frame_0001.jpg")],
        provider="dashscope",
        model="qwen-vl-max",
        title="Demo",
    )

    content = path.read_text(encoding="utf-8")
    assert "vision_model: qwen-vl-max" in content
    assert read_visual_notes_text(path) == "# Visual Notes\n\nvisible text and scenes"
