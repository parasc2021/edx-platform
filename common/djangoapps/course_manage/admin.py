"""Django admin interface for course_manage models. """
from django.contrib import admin
from .models import *


class CourseManageAdmin(admin.ModelAdmin):
    """Admin Interface for CourseManage model."""

    raw_id_fields = ["course"]
    list_display = ["course"]
    search_fields = ["course__id"]


admin.site.register(CourseManage, CourseManageAdmin)
