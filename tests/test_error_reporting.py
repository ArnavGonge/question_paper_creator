import logging

from qpc.error_reporting import AppConfigurationError, report_operation_error


def test_configuration_error_is_safe_and_logged_with_reference(caplog):
    logger = logging.getLogger("qpc.test.configuration")
    error = AppConfigurationError("openai")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error("topic_extraction", error, logger=logger)

    assert report.user_message == (
        "AI features are not configured on this server. Contact the app administrator."
    )
    assert report.reference_id in caplog.text


def test_unexpected_error_hides_exception_from_user_and_log(caplog):
    logger = logging.getLogger("qpc.test.unexpected")
    error = RuntimeError("provider payload must remain private")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error("paper_generation", error, logger=logger)

    assert report.user_message == (
        "The paper could not be generated. Please try again in a moment."
    )
    assert "provider payload" not in report.user_message
    assert "provider payload" not in caplog.text
    assert report.reference_id in caplog.text
    assert "Traceback" in caplog.text


def test_timeout_gets_specific_retry_guidance(caplog):
    class APITimeoutError(Exception):
        pass

    logger = logging.getLogger("qpc.test.timeout")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report = report_operation_error(
            "paper_generation",
            APITimeoutError("private provider detail"),
            logger=logger,
        )

    assert report.user_message == (
        "The AI service did not respond in time. Please try again."
    )


def test_error_log_context_uses_filename_without_document_content(caplog):
    logger = logging.getLogger("qpc.test.pdf")

    with caplog.at_level(logging.ERROR, logger=logger.name):
        report_operation_error(
            "pdf_extraction",
            ValueError("broken xref"),
            context={"filename": "chapter.pdf"},
            logger=logger,
        )

    assert "chapter.pdf" in caplog.text
    assert "document_text" not in caplog.text
