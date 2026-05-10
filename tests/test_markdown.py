from seed.markdown import find_markdown_field, read_markdown_body, read_markdown_metadata, split_frontmatter


def test_split_frontmatter_returns_metadata_and_body():
    metadata, body = split_frontmatter("---\ntitle: Demo\nowner: UP\n---\n\n# Body")

    assert metadata == {"title": "Demo", "owner": "UP"}
    assert body.strip() == "# Body"


def test_read_markdown_body_strips_frontmatter(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("---\ntitle: Demo\n---\n\n# Body", encoding="utf-8")

    assert read_markdown_body(path) == "# Body"


def test_read_markdown_metadata_handles_missing_frontmatter(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("# Body", encoding="utf-8")

    assert read_markdown_metadata(path) == {}


def test_find_markdown_field_supports_frontmatter_and_markdown_metadata():
    assert find_markdown_field("---\nowner: Demo UP\n---\nbody", "owner") == "Demo UP"
    assert find_markdown_field("## Metadata\n\n- Owner: Demo UP", "owner") == "Demo UP"
    assert find_markdown_field("Owner: Demo UP", "owner") == "Demo UP"
