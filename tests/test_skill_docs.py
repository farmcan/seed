from pathlib import Path


def test_video_skills_share_analysis_lenses():
    lens_path = Path("skills/video-semantics-analyzer/references/video-analysis-lenses.md")

    assert lens_path.exists()
    assert "Fabric" in lens_path.read_text(encoding="utf-8")
    assert "BiliNote" in lens_path.read_text(encoding="utf-8")
    assert "video-analysis-lenses.md" in Path(
        "skills/video-semantics-analyzer/SKILL.md"
    ).read_text(encoding="utf-8")
    assert "video-analysis-lenses.md" in Path("skills/video-note-summarizer/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "video-analysis-lenses.md" in Path(
        "skills/creator-profile-aggregator/SKILL.md"
    ).read_text(encoding="utf-8")
