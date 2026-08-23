from dataclasses import dataclass

from qpc.schemas import GeneratedPaper, PaperBlueprint, QuestionType


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    section_label: str = ""

def validate_generated_paper(
    blueprint: PaperBlueprint, paper: GeneratedPaper
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_by_label = {section.label: section for section in blueprint.sections}
    generated_by_label = {section.label: section for section in paper.sections}

    for blueprint_section in blueprint.sections:
        generated_section = generated_by_label.get(blueprint_section.label)
        if generated_section is None:
            issues.append(
                ValidationIssue(
                    code="missing_section",
                    message=f"{blueprint_section.label} is missing from generated paper.",
                    section_label=blueprint_section.label,
                )
            )
            continue

        if generated_section.question_type != blueprint_section.question_type:
            issues.append(
                ValidationIssue(
                    code="section_type_mismatch",
                    message=f"{blueprint_section.label} should be {blueprint_section.question_type}.",
                    section_label=blueprint_section.label,
                )
            )

        expected_question_count = expected_generated_question_count(
            blueprint_section.question_type,
            blueprint_section.questions_to_generate,
        )
        if len(generated_section.questions) != expected_question_count:
            issues.append(
                ValidationIssue(
                    code="question_count_mismatch",
                    message=(
                        f"{blueprint_section.label} should contain "
                        f"{expected_question_count} questions."
                    ),
                    section_label=blueprint_section.label,
                )
            )

        if (
            blueprint_section.question_type is QuestionType.CASE_STUDY
            and not generated_section.passage.strip()
        ):
            issues.append(
                ValidationIssue(
                    code="missing_case_study_passage",
                    message=f"{blueprint_section.label} needs a case-study passage.",
                    section_label=blueprint_section.label,
                )
            )

        for question in generated_section.questions:
            if len(question.text.strip()) < 8:
                issues.append(
                    ValidationIssue(
                        code="question_too_short",
                        message=f"{blueprint_section.label} contains an empty or too-short question.",
                        section_label=blueprint_section.label,
                    )
                )
            if (
                blueprint_section.question_type is QuestionType.MCQ
                and len(question.options) != 4
            ):
                issues.append(
                    ValidationIssue(
                        code="mcq_option_count",
                        message=f"{blueprint_section.label} MCQs must have exactly four options.",
                        section_label=blueprint_section.label,
                    )
                )
            if (
                blueprint_section.question_type is QuestionType.MATCH
                and len(question.pairs) != blueprint_section.questions_to_generate
            ):
                issues.append(
                    ValidationIssue(
                        code="match_pair_count",
                        message=(
                            f"{blueprint_section.label} should contain "
                            f"{blueprint_section.questions_to_generate} match pairs."
                        ),
                        section_label=blueprint_section.label,
                    )
                )
            if (
                blueprint_section.question_type is QuestionType.CASE_STUDY
                and len(question.sub_questions) != blueprint_section.questions_to_generate
            ):
                issues.append(
                    ValidationIssue(
                        code="case_study_sub_question_count",
                        message=(
                            f"{blueprint_section.label} should contain "
                            f"{blueprint_section.questions_to_generate} case-study sub-questions."
                        ),
                        section_label=blueprint_section.label,
                    )
                )
            if question.question_type != blueprint_section.question_type:
                issues.append(
                    ValidationIssue(
                        code="question_type_mismatch",
                        message=f"{blueprint_section.label} contains a question with the wrong type.",
                        section_label=blueprint_section.label,
                    )
                )

    extra_labels = set(generated_by_label) - set(expected_by_label)
    for label in sorted(extra_labels):
        issues.append(
            ValidationIssue(
                code="unexpected_section",
                message=f"{label} was generated but is not in the blueprint.",
                section_label=label,
            )
        )

    return issues


def expected_generated_question_count(
    question_type: QuestionType, configured_count: int
) -> int:
    if question_type in {QuestionType.MATCH, QuestionType.CASE_STUDY}:
        return 1
    return configured_count
