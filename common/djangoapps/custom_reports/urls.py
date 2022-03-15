"""
URLs for the Custom Report app.
"""
from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r"^grade-data", grade_data, name="grade_data"),
    url(r"^get/grade-data/$", get_grade_data, name="get_grade_data"),
    url(
        r"^generate/grade-data/report/$",
        generate_grade_data_report,
        name="generate_grade_data_report",
    ),
    url(
        r"^get/grade-data/report/$",
        get_grade_data_report,
        name="get_grade_data_report",
    ),
    url(r"^program-data", program_data, name="program_data"),
    url(
        r"^generate/program-data/report/$",
        generate_program_data_report,
        name="generate_program_data_report",
    ),
    url(
        r"^get/program-data/report/$",
        get_program_data_report,
        name="get_program_data_report",
    ),
]
