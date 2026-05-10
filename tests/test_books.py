from seed.books import (
    book_note_output_path,
    book_semantics_output_path,
    extract_key_points,
    topic_profile_output_path,
    write_book_note,
    write_book_semantics,
    write_topic_profile,
)


def test_book_output_paths(tmp_path):
    assert book_note_output_path(library_root=tmp_path, author="Author", title="My Book") == (
        tmp_path / "notes" / "author-my-book.book-note.md"
    )
    assert book_semantics_output_path(library_root=tmp_path, author="Author", title="My Book") == (
        tmp_path / "semantics" / "author-my-book.book-semantics.md"
    )
    assert topic_profile_output_path(library_root=tmp_path, topic="Decision") == (
        tmp_path / "distilled" / "decision.topic-profile.md"
    )


def test_write_book_note_and_semantics(tmp_path):
    source = tmp_path / "note.md"
    source.write_text("- Principle A\n- Principle B", encoding="utf-8")
    note = write_book_note(
        tmp_path / "book-note.md",
        source_path=source,
        author="Author",
        title="Book",
        location="ch1",
    )
    semantics = write_book_semantics(
        tmp_path / "book-semantics.md",
        note_path=note,
        author="Author",
        title="Book",
        topic="Decision",
    )

    note_text = note.read_text(encoding="utf-8")
    semantics_text = semantics.read_text(encoding="utf-8")
    assert "source_type: book-note" in note_text
    assert "- Principle A" in semantics_text
    assert "## Agent Checks" in semantics_text


def test_write_topic_profile(tmp_path):
    semantics = tmp_path / "book-semantics.md"
    semantics.write_text("# Book Semantics\n\n## Key Points\n\n- A", encoding="utf-8")

    output = write_topic_profile(tmp_path / "topic.md", topic="Decision", semantics_paths=[semantics])

    assert "Topic Profile: Decision" in output.read_text(encoding="utf-8")


def test_extract_key_points():
    assert extract_key_points("# Title\n\n- A\nB") == ["A", "B"]
