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
