from django.dispatch import receiver

from ..models import LeaderBoard
from .signals import CUSTOM_COURSE_GRADE_CHANGED


@receiver(CUSTOM_COURSE_GRADE_CHANGED)
def update_leaderboard(user, course, grade, **kwargs):
    points = grade.percent * 100
    passing_grade = course.lowest_passing_grade * 100
    leaderboard, _created = LeaderBoard.objects.get_or_create(
        user=user, course_id=course.id
    )
    leaderboard.score = points
    leaderboard.has_passed = True if points >= passing_grade else False
    leaderboard.save()
