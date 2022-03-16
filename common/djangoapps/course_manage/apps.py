"""
CourseManage Application Configuration

CourseManage Application signal handlers are connected here.
"""

from django.apps import AppConfig


class CourseManageConfig(AppConfig):
    """
    Application Configuration for CourseManage app.
    """

    name = "common.djangoapps.course_manage"
    verbose_name = "Course Manage"

    def ready(self):
        """
        Connect handlers to signals.
        """
        # Can't import models at module level in AppConfigs, and models get
        # included from the signal handlers
        from .signals import handlers  # pylint: disable=unused-variable
