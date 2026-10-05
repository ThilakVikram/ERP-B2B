"""Exceptions raised by the Amazon SP-API integration."""


class AmazonIntegrationError(Exception):
    """Base error for everything raised by app.integration.amazon."""


class AmazonConfigError(AmazonIntegrationError):
    """Credentials / settings are missing or invalid."""


class AmazonApiError(AmazonIntegrationError):
    """SP-API returned an error response (after retries were exhausted)."""

    def __init__(self, message: str, status: int | None = None, body: str | bytes | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


class ReportProcessingError(AmazonIntegrationError):
    """A report finished as FATAL or CANCELLED instead of DONE."""

    def __init__(self, report_id: str, processing_status: str, details: str | None = None):
        msg = f"Report {report_id} finished with status {processing_status}"
        if details:
            msg += f": {details}"
        super().__init__(msg)
        self.report_id = report_id
        self.processing_status = processing_status
        self.details = details


class ReportTimeoutError(AmazonIntegrationError):
    """A report did not finish processing within the allowed time."""


class QueryProcessingError(ReportProcessingError):
    """A Data Kiosk query finished as FATAL or CANCELLED instead of DONE.

    Subclasses ReportProcessingError so the job queue (job_queue_service) handles both the same way.
    """

    def __init__(self, query_id: str, processing_status: str, details: str | None = None):
        super().__init__(query_id, processing_status, details)
        self.args = (
            f"Data Kiosk query {query_id} finished with status {processing_status}" + (f": {details}" if details else ""),
        )
        self.query_id = query_id
