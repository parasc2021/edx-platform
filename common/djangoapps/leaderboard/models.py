"""
Models for Leaderboard Information

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms makemigrations --settings=production leaderboard
3. ./manage.py lms migrate --settings=production leaderboard
"""
from django.db import models

from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField


class LeaderBoard(TimeStampedModel):
    """
    Model for store course wise score
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    score = models.FloatField(max_length=255, null=True)
    has_passed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Leaderboard"
        verbose_name_plural = "Leaderboard"

    def __str__(self):
        return self.user.email

    @classmethod
    def get_score(cls, user, course_key):
        """
        Returen score for given user and course id.
        """
        try:
            leaderboard = cls.objects.get(user=user, course_id=course_key)
            return leaderboard.score
        except Exception as e:
            return 0.00


class Batch(TimeStampedModel):
    """
    Model for store Batches
    """

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"

    def __str__(self):
        return self.name
