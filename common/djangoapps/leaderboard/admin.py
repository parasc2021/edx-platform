"""Django admin interface for Leaderboard models. """

from django.contrib import admin
from .models import *


class LeaderBoardAdmin(admin.ModelAdmin):
    """
    Admin Interface for Leaderboard Model
    """

    list_display = ["user", "course_id", "score", "has_passed"]
    search_fields = ["user__username"]


class BatchAdmin(admin.ModelAdmin):
    """
    Admin Interface for Batch Model
    """

    list_display = ["name"]


admin.site.register(Batch, BatchAdmin)

admin.site.register(LeaderBoard, LeaderBoardAdmin)
