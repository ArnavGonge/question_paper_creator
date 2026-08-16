from qpc.demo_data import default_blueprint
from qpc.schemas import QuestionType


def test_default_blueprint_starts_with_one_editable_section():
    blueprint = default_blueprint()

    assert blueprint.metadata.max_marks == 4
    assert blueprint.total_marks() == 4
    assert len(blueprint.sections) == 1
    assert [section.question_type for section in blueprint.sections] == [
        QuestionType.MCQ,
    ]
