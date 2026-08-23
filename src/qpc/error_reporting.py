from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from uuid import uuid4


LOGGER = logging.getLogger("qpc")


class AppConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ErrorReport:
    user_message: str
    reference_id: str


OPERATION_MESSAGES = {
    "pdf_extraction": (
        "This PDF could not be read. Check that it opens normally and is not "
        "password protected."
    ),
    "topic_extraction": (
        "Topics could not be found right now. Please try again in a moment."
    ),
    "paper_generation": (
        "The paper could not be generated. Please try again in a moment."
    ),
    "section_generation": (
        "This section could not be regenerated. Please try again in a moment."
    ),
    "document_export": (
        "The Word document could not be prepared. Please try again."
    ),
}


def report_operation_error(
    operation: str,
    error: Exception,
    *,
    context: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> ErrorReport:
    reference_id = uuid4().hex[:8].upper()
    error_type = type(error).__name__
    if isinstance(error, AppConfigurationError) or error_type == "AuthenticationError":
        message = (
            "AI features are not configured on this server. "
            "Contact the app administrator."
        )
    elif error_type in {"APITimeoutError", "APIConnectionError"}:
        message = "The AI service did not respond in time. Please try again."
    elif error_type == "RateLimitError":
        message = "The AI service is busy right now. Please wait a moment and retry."
    elif error_type in {"JSONDecodeError", "ValidationError"} and operation in {
        "topic_extraction",
        "paper_generation",
        "section_generation",
    }:
        message = "The AI response was incomplete. Please generate it again."
    else:
        message = OPERATION_MESSAGES.get(
            operation,
            "Something went wrong. Please try again.",
        )

    active_logger = logger or LOGGER
    active_logger.error(
        (
            "operation_failed reference_id=%s operation=%s context=%r "
            "error_type=%s\nTraceback:\n%s"
        ),
        reference_id,
        operation,
        context or {},
        error_type,
        "".join(traceback.format_tb(error.__traceback__)),
    )
    return ErrorReport(user_message=message, reference_id=reference_id)
