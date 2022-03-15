"""Django admin interface for Custom report models. """

from django.apps import AppConfig


class CustomReportConfig(AppConfig):
    name = "common.djangoapps.custom_reports"

    def ready(self):
        """
        Connect handlers to recalculate ranks.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from .signals import handlers  # pylint: disable=unused-variable
