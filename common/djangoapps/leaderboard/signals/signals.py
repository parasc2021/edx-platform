"""
Leaderboard related signals.
"""
from django.dispatch import Signal


CUSTOM_COURSE_GRADE_CHANGED = Signal(
    providing_args=[
        "user",  # User object
        "course",  # Course object
        "grade",  # Course Grade object
    ]
)
