"""
URLs for the Course Manage app.
"""
from django.conf.urls import url
from django.conf import settings

from .views import *

urlpatterns = [
    url(
        r"^site-manage/courses$",
        CoursesView.as_view(),
        name="courses-view",
    ),
    url(
        r"^site-manage/courses/{}/view/$".format(settings.COURSE_ID_PATTERN),
        CourseDetailView.as_view(),
        name="course-details-view",
    ),
    url(
        r"^site-manage/courses/update/unit/$",
        UpdateUnitView.as_view(),
        name="unit-update-view",
    ),
    url(
        r"^site-manage/courses/{}/(?P<unit_id>.*)/attendance/$".format(
            settings.COURSE_ID_PATTERN
        ),
        StudentAttendanceView.as_view(),
        name="student-attendance",
    ),
]
