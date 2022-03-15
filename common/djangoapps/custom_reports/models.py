"""
Models for Custom Report Information

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms makemigrations --settings=production custom_report
3. ./manage.py lms migrate --settings=production custom_report
"""
from django.db import models

from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
