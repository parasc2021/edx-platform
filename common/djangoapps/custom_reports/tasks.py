"""
This file contains celery tasks
"""
import os
import csv
import logging
import time
import itertools
from collections import OrderedDict
import datetime as default_datetime
from datetime import datetime, timedelta, date

from celery.task import task
from django.db.models import Q
from django.contrib.auth.models import User
from django.conf import settings

from xmodule.modulestore.django import modulestore
from lms.djangoapps.instructor.views.gradebook_api import get_grade_book_page
from lms.djangoapps.instructor.utils import get_module_for_student
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.instructor.utils import check_sga_in_subsection
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.models import CourseAccessRole
from common.djangoapps.course_manage.models import CourseManage
from common.djangoapps.leaderboard.models import LeaderBoard, Batch
from .helpers import get_course_status

log = logging.getLogger(__name__)


def validate_directory(dir_path):
    """
    Create directory if not exixt and return
    """
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    return os.chdir(dir_path)


def write_csv_file(filename, data):
    """
    Write data into given csv file.
    """
    with open(filename, "w") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        writer.writerows(data)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def generate_grade_report_csv(username, batch):
    staff_user = User.objects.get(username=username)
    batch = Batch.objects.get(id=batch)
    report_dir = "custom_reports/{username}/grade_data".format(username=str(username))
    dir_path = "{media_root}{report_dir}/".format(
        media_root=settings.MEDIA_ROOT, report_dir=report_dir
    )
    validate_directory(dir_path)
    current_time = time.strftime("%d_%m_%Y__%H_%M_%S")
    file_name = "GRADE_REPORT_{batch}_{time}.csv".format(
        batch=batch.name, time=current_time
    )
    file_path = dir_path + file_name

    users = User.objects.filter(is_active=True, profile__batch=batch).order_by(
        "username"
    )
    courses = CourseManage.objects.filter(batch=batch).order_by("course__display_name")
    courses = [course_mange.course for course_mange in courses]
    course_ids = [course.id for course in courses]
    admin_users = set(
        CourseAccessRole.objects.filter(course_id__in=course_ids).values_list("user")
    )
    admin_users = list(itertools.chain(*admin_users))
    users = users.exclude(
        Q(is_staff=True) | Q(is_superuser=True) | Q(id__in=admin_users)
    )
    header_data = [
        "",
    ]
    for course in courses:
        header_data.append(course.display_name)
    header_data.append("Total(%)")

    row_data = [header_data]
    for user in users:
        student_info = [user.username]
        total_score = 0
        for course in courses:
            score = LeaderBoard.get_score(user, course.id)
            status = get_course_status(staff_user, course.id, user)
            if status:
                student_info.append("{} ({})".format(score, status))
            else:
                student_info.append(score)
            try:
                course_manage = CourseManage.objects.get(course_id=course.id)
                weighted_score = (score * float(course_manage.weight)) / 100
                total_score += weighted_score
            except Exception as e:
                total_score += 0
        student_info.append(total_score)
        row_data.append(student_info)
    write_csv_file(file_path, row_data)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def generate_program_report_csv(username, batch):
    user = User.objects.get(username=username)
    batch = Batch.objects.get(id=batch)

    report_dir = "custom_reports/{username}/program_details".format(
        username=str(username)
    )
    dir_path = "{media_root}{report_dir}/".format(
        media_root=settings.MEDIA_ROOT, report_dir=report_dir
    )
    validate_directory(dir_path)
    current_time = time.strftime("%d_%m_%Y__%H_%M_%S")
    file_name = "DETAILED_REPORT_{batch}_{time}.csv".format(
        batch=batch.name, time=current_time
    )
    file_path = dir_path + file_name

    users = User.objects.filter(is_active=True, profile__batch=batch).order_by(
        "username"
    )
    courses = CourseManage.objects.filter(batch=batch).order_by("course__display_name")
    courses = [course_mange.course for course_mange in courses]
    course_ids = [course.id for course in courses]
    admin_users = set(
        CourseAccessRole.objects.filter(course_id__in=course_ids).values_list("user")
    )
    admin_users = list(itertools.chain(*admin_users))
    users = users.exclude(
        Q(is_staff=True) | Q(is_superuser=True) | Q(id__in=admin_users)
    )
    row_data = []
    for student in users:
        student_info = [student.username]
        header_data = [
            "",
        ]
        course_header = [
            "",
        ]
        for course in courses:
            course_header.append(course.display_name)
            course_key = course.id
            course = get_course_with_access(user, "staff", course_key, depth=None)
            with modulestore().bulk_operations(course.location.course_key):
                course_grade = CourseGradeFactory().read(student, course)
                courseware_summary = course_grade.customized_chapter_grades
                grade_summary = course_grade.summary

            header_data.append("Total")
            total_score = "{0:.0f}%".format(100 * grade_summary["percent"])
            student_info.append(total_score)
            for chapter in courseware_summary:
                if not chapter["display_name"] == "hidden":
                    for section in chapter["sections"]:
                        if section.graded and not check_sga_in_subsection(
                            section.location, user
                        ):
                            header_data.append(section.display_name)
                            earned = section.all_total.earned
                            total = section.all_total.possible
                            score = (
                                "{0:.0%}".format(float(earned) / total)
                                if earned > 0 and total > 0
                                else 0
                            )
                            student_info.append(score)
                            course_header.append("")
            sumbission_msg = "NS"
            sga_blocks = modulestore().get_items(
                course_key, qualifiers={"category": "edx_sga"}
            )
            sga_blocks.sort(key=lambda x: x.display_name)
            for block in sga_blocks:
                module = get_module_for_student(student, block.location)
                header_data.append(block.display_name)
                if module:
                    if not module.student_state().get("uploaded", None):
                        sumbission_msg = "NS"
                    elif module.score:
                        sumbission_msg = "{0:.0f}%".format(module.score)
                    else:
                        sumbission_msg = "NG"
                student_info.append(sumbission_msg)
                course_header.append("")
            header_data.append("")
            student_info.append("")
            course_header.append("")
        row_data.append(student_info)
    csv_data = [course_header, header_data]
    csv_data += row_data
    write_csv_file(file_path, csv_data)
