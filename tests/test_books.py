import json

from seed.books import (
    book_author_homepage_output_path,
    book_author_profile_output_path,
    book_homepage_output_path,
    book_layers_output_path,
    book_methods_output_path,
    book_note_output_path,
    book_semantics_output_path,
    build_book_author_profile_artifact,
    build_book_layer_artifact,
    build_book_methods_prompt,
    extract_key_points,
    find_author_book_method_paths,
    topic_profile_output_path,
    write_book_author_homepage_html,
    write_book_author_profile_artifact,
    write_book_homepage_html,
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
    assert book_homepage_output_path(library_root=tmp_path, author="Author", title="My Book") == (
        tmp_path / "reports" / "author-my-book.book-homepage.html"
    )
    assert book_author_profile_output_path(library_root=tmp_path, author="Author") == (
        tmp_path / "distilled" / "author.book-author-profile.json"
    )
    assert book_author_homepage_output_path(library_root=tmp_path, author="Author") == (
        tmp_path / "reports" / "author.book-author-homepage.html"
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


def sample_methods(author: str, title: str, topic: str | None = None) -> dict:
    return {
        "version": 1,
        "kind": "book_methods",
        "author": author,
        "title": title,
        "topic": topic,
        "generated_at": "2026-05-18T00:00:00+00:00",
        "summary": f"{title} summary",
        "stable_principles": [
            {
                "principle": "Check the boundary",
                "why_it_matters": "It keeps the method honest.",
                "evidence_refs": ["B1"],
            }
        ],
        "decision_rules": [
            {
                "rule": "Use the method only when inputs are visible.",
                "when_to_use": "Before applying a framework.",
                "evidence_refs": ["B2"],
            }
        ],
        "mental_models": [{"model": "Boundary map", "explanation": "Track fit and limits.", "evidence_refs": ["B3"]}],
        "agent_checks": [{"check": "Is the boundary explicit?", "purpose": "Avoid overreach.", "evidence_refs": ["B1"]}],
        "cross_source_hooks": [
            {
                "hook": "Compare claims against boundary conditions.",
                "how_to_use": "Use when reviewing UP/video claims.",
                "evidence_refs": ["B2"],
            }
        ],
        "source_gaps": ["Need page locations."],
        "open_questions": ["Does this transfer to videos?"],
    }


def write_methods(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_write_book_homepage_html(tmp_path):
    source = tmp_path / "book-source.json"
    layers = tmp_path / "book-layers.json"
    methods = tmp_path / "book-methods.json"
    source.write_text('{"entries": [{"evidence_id": "B1"}], "source_gaps": ["missing page"]}', encoding="utf-8")
    layers.write_text(
        '{"blocks": [{"ref": "B1"}], "sections": [{"title": "Chapter", "evidence_refs": ["B1"], "block_count": 1, "summary_candidate": "A section.", "method_candidates": []}]}',
        encoding="utf-8",
    )
    write_methods(methods, sample_methods("Author", "Book", "Decision"))

    output = write_book_homepage_html(
        tmp_path / "book-homepage.html",
        author="Author",
        title="Book",
        topic="Decision",
        source_path=source,
        layers_path=layers,
        methods_path=methods,
    )

    html = output.read_text(encoding="utf-8")
    assert "Book Homepage" in html
    assert "Check the boundary" in html
    assert "book-source" in html
    assert "Chapter" in html


def test_book_author_profile_and_homepage(tmp_path):
    first = book_methods_output_path(library_root=tmp_path, author="Author", title="First")
    second = book_methods_output_path(library_root=tmp_path, author="Author", title="Second")
    write_methods(first, sample_methods("Author", "First", "Decision"))
    write_methods(second, sample_methods("Author", "Second", "Decision"))

    found = find_author_book_method_paths(library_root=tmp_path, author="Author", topic="Decision")
    profile = build_book_author_profile_artifact(author="Author", methods_paths=found, topic="Decision")
    profile_path = write_book_author_profile_artifact(tmp_path / "author-profile.json", profile)
    homepage = write_book_author_homepage_html(tmp_path / "author-homepage.html", profile_path=profile_path)

    assert len(profile["books"]) == 2
    assert profile["recurring_principles"][0]["principle"] == "Check the boundary"
    html = homepage.read_text(encoding="utf-8")
    assert "Book Author Homepage" in html
    assert "First" in html
    assert "Second" in html
