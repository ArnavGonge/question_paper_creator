import pytest

from qpc.demo_data import default_sections
from qpc.schemas import QuestionType, SectionBlueprint, SourceDocument, SourcePage
from qpc.workflow import (
    append_default_section,
    delete_section,
    documents_after_extraction,
    move_section,
    next_section_label,
)


def section(label: str) -> SectionBlueprint:
    return SectionBlueprint(
        label=label,
        heading=f"{label} heading",
        question_type=QuestionType.SHORT,
        questions_to_generate=2,
        questions_to_answer=2,
        marks_per_question=2,
    )


def test_failed_reextraction_keeps_previous_documents():
    previous = [
        SourceDocument(
            filename="working.pdf",
            pages=[SourcePage(page_number=1, text="Working text")],
        )
    ]

    assert documents_after_extraction(previous, []) == previous


def test_successful_reextraction_replaces_previous_documents():
    previous = [SourceDocument(filename="old.pdf", pages=[])]
    extracted = [SourceDocument(filename="new.pdf", pages=[])]

    assert documents_after_extraction(previous, extracted) == extracted


def test_move_section_returns_reordered_copies_without_relabelling():
    sections = [section("Section A"), section("Section B"), section("Section C")]

    moved = move_section(sections, 1, -1)

    assert [item.label for item in moved] == ["Section B", "Section A", "Section C"]
    assert [item.label for item in sections] == ["Section A", "Section B", "Section C"]
    assert moved[0] is not sections[1]


@pytest.mark.parametrize(
    ("index", "offset", "message"),
    [
        (0, -1, "section cannot move beyond the list"),
        (2, 1, "section cannot move beyond the list"),
        (1, 2, "invalid section move"),
        (4, -1, "invalid section move"),
    ],
)
def test_move_section_rejects_invalid_boundaries(index, offset, message):
    sections = [section("Section A"), section("Section B"), section("Section C")]

    with pytest.raises(ValueError, match=message):
        move_section(sections, index, offset)


def test_delete_section_rejects_deleting_the_last_section():
    with pytest.raises(ValueError, match="at least one section"):
        delete_section(default_sections(), 0)


def test_delete_section_removes_only_the_requested_section():
    sections = [section("Section A"), section("Section B"), section("Section C")]

    remaining = delete_section(sections, 1)

    assert [item.label for item in remaining] == ["Section A", "Section C"]


def test_delete_section_rejects_an_invalid_index():
    with pytest.raises(ValueError, match="invalid section index"):
        delete_section([section("Section A"), section("Section B")], 4)


def test_new_section_uses_first_available_label_after_a_gap():
    sections = [section("Section A"), section("Section C")]

    assert next_section_label(sections) == "Section B"
    assert append_default_section(sections)[-1].label == "Section B"
