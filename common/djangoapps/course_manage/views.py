import json
import logging
from datetime import datetime

from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse, Http404
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from completion.models import BlockCompletion
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey, UsageKey
from edxmako.shortcuts import render_to_response, render_to_string
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_experience.utils import get_course_outline_block_tree
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.user_manage.decorators import ensure_coordinator_or_pa_access

from .models import *


log = logging.getLogger(__name__)


class CoursesView(View):
    @method_decorator(login_required)
    @method_decorator(ensure_coordinator_or_pa_access)
    def dispatch(self, request, **kwargs):
        self.hub = request.user.usermanage.hub
        self.DETAILS_TO_DISPLAY = [
            "Course Name",
            "Start Date",
            "End Date",
        ]

        save_change_button_id = request.POST.get("save-change-id", "")
        return super(CoursesView, self).dispatch(request)

    def get(self, request):
        """
        Fetches all the user registered on the Site.
        """
        courses = CourseManage.objects.filter(hub=self.hub, course_type="long")
        if request.user.usermanage.is_course_coordinator:
            courses = CourseManage.get_my_lms_courses(request.user)

        self.context = {
            "courses": courses,
            "details_to_display": self.DETAILS_TO_DISPLAY,
        }

        return render_to_response(
            "site-manage/course-management/courses.html", self.context
        )


class CourseDetailView(View):
    @method_decorator(login_required)
    @method_decorator(ensure_coordinator_or_pa_access)
    def get(self, request, course_id):
        try:
            course_key = CourseKey.from_string(course_id)
            course = CourseOverview.objects.get(id=course_key)
        except Exception as e:
            raise Http404("Invalid Course id")

        course_block_tree = get_course_outline_block_tree(
            request, course_id, request.user
        )
        course_sections = course_block_tree.get("children")
        modules = list()
        if course_sections:
            modules = course_sections[0].get("children")

        self.context = {"course": course, "modules": modules}
        return render_to_response(
            "site-manage/course-management/course-details.html", self.context
        )


class UpdateUnitView(View):
    @method_decorator(login_required)
    @method_decorator(ensure_coordinator_or_pa_access)
    def post(self, request):
        data_dict = request.POST.dict()
        save_change_button_id = data_dict.get("save-change-id", "")
        course_id = data_dict.get("course_id")
        unit_id = data_dict.get("unit_id")
        try:
            course_key = CourseKey.from_string(course_id)
        except Exception as e:
            return JsonResponse(
                status=400,
                data={
                    "errorMsg": "Invalid Course ID",
                    "divId": "unit_details .update-unit-error",
                    "saveChangeId": save_change_button_id,
                },
            )

        unit_date = data_dict.get("unit_date")
        if unit_date != "":
            try:
                unit_date_obj = datetime.strptime(unit_date, "%d-%m-%Y").date()
                data_dict.update({"start": unit_date_obj})
            except Exception as e:
                return JsonResponse(
                    status=400,
                    data={
                        "errorMsg": "Invalid date format",
                        "divId": "unit_details .update-unit-error",
                        "saveChangeId": save_change_button_id,
                    },
                )
        try:
            CourseUnitTimeLine.create_or_update(course_key, unit_id, data_dict)
            return JsonResponse(
                status=200,
                data={
                    "message": "{} unit details updated successfully.".format(
                        data_dict.get("unit_name")
                    ),
                    "data": "createuser",
                },
            )
        except Exception as e:
            log.error(str(e))
            return JsonResponse(
                status=400,
                data={
                    "errorMsg": "Something went wrong",
                    "divId": "unit_details .update-unit-error",
                    "saveChangeId": save_change_button_id,
                },
            )


class StudentAttendanceView(View):
    @method_decorator(login_required)
    @method_decorator(ensure_coordinator_or_pa_access)
    def get(self, request, course_id, unit_id):
        try:
            course_key = CourseKey.from_string(course_id)
            course = CourseOverview.objects.get(id=course_key)
        except Exception as e:
            raise Http404("Invalid Course id")

        try:
            usage_key = UsageKey.from_string(unit_id)
            unit = modulestore().get_item(usage_key)
        except Exception as e:
            raise Http404("Invalid Unit id")

        officers = CourseEnrollment.objects.users_enrolled_in(course_key)
        submitted_attendance = ModuleAttendance.objects.filter(
            course_id=course_key, unit_id=unit.scope_ids.usage_id
        ).values_list("user_id", flat=True)
        paginator = Paginator(officers, 50)
        page = request.GET.get("page")

        try:
            officers = paginator.page(page)
        except PageNotAnInteger:
            officers = paginator.page(1)
        except EmptyPage:
            officers = paginator.page(paginator.num_pages)

        self.context = {
            "students": officers,
            "course": course,
            "unit": unit,
            "submitted_attendance": submitted_attendance,
        }

        return render_to_response(
            "site-manage/course-management/attendace-details.html", self.context
        )

    @method_decorator(login_required)
    @method_decorator(ensure_coordinator_or_pa_access)
    def post(self, request, course_id, unit_id):
        try:
            course_key = CourseKey.from_string(course_id)
            course = CourseOverview.objects.get(id=course_key)
        except Exception as e:
            raise Http404("Invalid Course id")

        try:
            usage_key = UsageKey.from_string(unit_id)
            unit = modulestore().get_item(usage_key)
        except Exception as e:
            raise Http404("Invalid Unit id")

        data = request.POST.dict()
        student_ids = json.loads(data.get("student_ids"))
        students = User.objects.filter(id__in=student_ids)
        attendance = ModuleAttendance.objects.filter(
            course_id=course_key, unit_id=unit.scope_ids.usage_id
        )
        attendance.delete()
        for user in students:
            for block in unit.get_children():
                BlockCompletion.objects.submit_completion(
                    user=user,
                    block_key=block.scope_ids.usage_id,
                    completion=1.0,
                )
            ModuleAttendance.create_or_update(course.id, unit.scope_ids.usage_id, user)
        return JsonResponse(
            status=200,
            data={
                "reload": True,
                "reload_url": reverse(
                    "student-attendance", args=[str(course.id), str(unit.location)]
                ),
                "message": "Attendace details updated successfully",
            },
        )
