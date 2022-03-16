"""
    Manage signal handlers here
"""
import logging

from django.dispatch import receiver
from xmodule.modulestore.django import SignalHandler
from common.djangoapps.student.models import CourseEnrollment
from ..models import CourseManage

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(
    sender, course_key, **kwargs
):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    invalidates the corresponding Course cache entry if one exists.
    """
    CourseManage.objects.filter(course_id=course_key).delete()
    CourseEnrollment.objects.filter(course_id=course_key).delete()
