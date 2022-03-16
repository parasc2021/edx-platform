"""
Models for CourseManage Information

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms makemigrations --settings=production course_manage
3. ./manage.py lms migrate --settings=production course_manage
"""
import logging

from model_utils.models import TimeStampedModel
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.contrib.auth.models import User

from opaque_keys.edx.django.models import CourseKeyField
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.leaderboard.models import Batch

log = logging.getLogger(__name__)


def get_or_none(classmodel, **kwargs):
    """
    Return object if exist otherwise return None
    """
    try:
        return classmodel.objects.get(**kwargs)
    except Exception as e:
        return None


class CourseManage(TimeStampedModel):
    """
    Model for store course releted extra details
    """

    course = models.OneToOneField(
        CourseOverview,
        db_constraint=False,
        db_index=True,
        on_delete=models.CASCADE,
    )
    weight = models.CharField(blank=True, null=True, max_length=32)
    batch = models.ForeignKey(
        Batch, on_delete=models.CASCADE, blank=True, null=True, db_index=True
    )

    def __str__(self):
        return "{}".format(self.course_id)

    class Meta:
        verbose_name = "CourseManage"
        verbose_name_plural = "Course Manage"

    @classmethod
    def create_or_update(cls, course_id, data_dict):
        """
        Create or update Course Details.
        """
        batch = get_or_none(Batch, id=data_dict.get("batch"))
        course, created = cls.objects.get_or_create(course_id=course_id)
        course.weight = data_dict.get("weight")
        course.batch = batch
        course.save()

    def __enumerable_to_display(self, enumerables, enum_value):
        """Get the human readable value from an enumerable list of key-value pairs."""
        return dict(enumerables)[enum_value]
