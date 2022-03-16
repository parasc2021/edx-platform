import json
import logging

from django.contrib.auth.models import User
from django.conf import settings
from celery.task import task


log = logging.getLogger(__name__)
