from seed.books import (
    book_layers_output_path,
    book_note_output_path,
    book_semantics_output_path,
    build_book_layer_artifact,
    build_book_methods_prompt,
    extract_key_points,
    topic_profile_output_path,
    write_book_layer_artifact,
    write_book_note,
    write_book_source_artifact,
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
    assert book_layers_output_path(library_root=tmp_path, author="Author", title="My Book") == (
        tmp_path / "distilled" / "author-my-book.book-layers.json"
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


def test_build_book_layer_artifact_groups_blocks_by_heading(tmp_path):
    note = tmp_path / "note.md"
    note.write_text(
        """
        # Part One

        - Principle A should be checked.
        - Avoid shortcut B.

        ## Chapter Two

        Method C has a boundary.
        """,
        encoding="utf-8",
    )

    artifact = build_book_layer_artifact(note_path=note, author="Author", title="Book", topic="Decision")

    assert artifact["kind"] == "book_layers"
    assert [block["ref"] for block in artifact["blocks"]] == ["B1", "B2", "B3"]
    assert artifact["blocks"][0]["section_title"] == "Part One"
    assert artifact["blocks"][2]["heading_path"] == ["Part One", "Chapter Two"]
    assert len(artifact["sections"]) == 2
    assert artifact["sections"][0]["method_candidates"][0]["evidence_ref"] == "B1"
    assert artifact["book_layer"]["distillation_strategy"] == "section methods -> book methods -> topic profile"


def test_write_book_layer_artifact(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- Principle A", encoding="utf-8")
    artifact = build_book_layer_artifact(note_path=note, author="Author", title="Book")

    output = write_book_layer_artifact(tmp_path / "book-layers.json", artifact)

    assert '"kind": "book_layers"' in output.read_text(encoding="utf-8")


def test_book_methods_prompt_includes_layer_plan(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("# Chapter\n\n- Principle A should be checked.", encoding="utf-8")

    prompt = build_book_methods_prompt(note_path=note, author="Author", title="Book")

    assert "<book_layer_plan>" in prompt
    assert '"kind": "book_layers"' in prompt
    assert '"section_title": "Chapter"' in prompt


def test_write_book_source_artifact_keeps_heading_path(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("# Chapter\n\n- Principle A", encoding="utf-8")

    output = write_book_source_artifact(
        tmp_path / "book-source.json",
        note_path=note,
        author="Author",
        title="Book",
    )

    text = output.read_text(encoding="utf-8")
    assert '"chapter": "Chapter"' in text
    assert '"heading_path": [' in text
