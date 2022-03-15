"""
This file contains celery tasks
"""
import logging

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


log = logging.getLogger("leaderboard")
