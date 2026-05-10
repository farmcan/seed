from pathlib import Path


ALLOWED_DOCS = {
    Path("docs/architecture.md"),
    Path("docs/todos.md"),
    Path("docs/research-competitors.md"),
}


def test_docs_file_allowlist():
    docs = {path for path in Path("docs").rglob("*.md")}

    assert docs == ALLOWED_DOCS


def test_agent_guide_exists():
    assert Path("agents.md").exists()


def test_agent_guide_requires_feature_docs_updates():
    text = Path("agents.md").read_text(encoding="utf-8")

    assert "只要新增或改变主要功能，必须同步更新主入口文档" in text
    assert "docs/architecture.md" in text
    assert "docs/todos.md" in text
    assert "docs/research-competitors.md" in text
