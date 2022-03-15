import os
import glob
import itertools

from django.db.models import Q
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from common.djangoapps.util.json_request import JsonResponse
from lms.djangoapps.instructor_analytics.csvs import create_csv_response

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.edxmako.shortcuts import render_to_response, render_to_string
from common.djangoapps.student.models import CourseAccessRole

from common.djangoapps.leaderboard.models import LeaderBoard, Batch
from common.djangoapps.course_manage.models import CourseManage
from .tasks import generate_program_report_csv, generate_grade_report_csv


@login_required
def grade_data(request):
    """
    Grade report including all courses
    """
    batches = Batch.objects.all().order_by("name")
    context = {"batches": batches}
    if request.user.is_staff or request.user.is_superuser:
        return render_to_response("custom_reports/grade-data.html", context)
    else:
        raise Http404()


@login_required
def get_grade_data(request):
    """
    Return Grade report including all courses in json format
    """
    batch = Batch.objects.get(id=request.POST.get("batch"))
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
    paginator = Paginator(users, 20)
    page = request.POST.get("page", 1)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    context = {"users": users, "courses": courses}
    template = render_to_string("custom_reports/table-data-grade.html", context)

    return JsonResponse({"data": template}, status=200)


@login_required
def generate_grade_data_report(request):
    """
    Return Grade report in CSV Format
    """
    if request.user.is_staff or request.user.is_superuser:
        generate_grade_report_csv.delay(
            request.user.username, request.POST.get("batch")
        )
    return JsonResponse({"Success": True}, status=200)


@login_required
def get_grade_data_report(request):
    report_dir = "custom_reports/{username}/grade_data/".format(
        username=str(request.user.username)
    )
    dir_path = "{media_root}{report_dir}/*".format(
        media_root=settings.MEDIA_ROOT, report_dir=report_dir
    )
    filelist = glob.glob(dir_path)
    files = list()
    for file in filelist:
        file_name = os.path.basename(file)
        file_link = "{}{}{}{}".format(
            settings.LMS_ROOT_URL, settings.MEDIA_URL, report_dir, file_name
        )
        files.append((file_name, file_link))

    files.reverse()
    return JsonResponse({"data": files}, status=200)


@login_required
def program_data(request):
    """
    Grade report including all courses
    """
    batches = Batch.objects.all().order_by("name")
    context = {"batches": batches}
    if request.user.is_staff or request.user.is_superuser:
        return render_to_response("custom_reports/program-data.html", context)
    else:
        raise Http404()


@login_required
def generate_program_data_report(request):
    """
    Return Program report in CSV Format
    """
    if request.user.is_staff or request.user.is_superuser:
        generate_program_report_csv.delay(
            request.user.username, request.POST.get("batch")
        )
    return JsonResponse({"Success": True}, status=200)


@login_required
def get_program_data_report(request):
    report_dir = "custom_reports/{username}/program_details/".format(
        username=str(request.user.username)
    )
    dir_path = "{media_root}{report_dir}/*".format(
        media_root=settings.MEDIA_ROOT, report_dir=report_dir
    )
    filelist = glob.glob(dir_path)
    files = list()
    for file in filelist:
        file_name = os.path.basename(file)
        file_link = "{}{}{}{}".format(
            settings.LMS_ROOT_URL, settings.MEDIA_URL, report_dir, file_name
        )
        files.append((file_name, file_link))

    files.reverse()
    return JsonResponse({"data": files}, status=200)
