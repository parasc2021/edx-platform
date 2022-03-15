from xmodule.modulestore.django import modulestore
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.instructor.utils import check_sga_in_subsection
from lms.djangoapps.grades.api import CourseGradeFactory


def get_course_status(staff_user, course_key, student):
    from lms.djangoapps.instructor.utils import get_module_for_student

    course = get_course_with_access(staff_user, "staff", course_key, depth=None)

    with modulestore().bulk_operations(course.location.course_key):
        course_grade = CourseGradeFactory().read(student, course)
        courseware_summary = course_grade.customized_chapter_grades

    sga_blocks = modulestore().get_items(course_key, qualifiers={"category": "edx_sga"})
    not_attempted = not_graded = False
    for block in sga_blocks:
        module = get_module_for_student(student, block.location)
        if module:
            if not module.student_state().get("uploaded", None):
                not_attempted = True
            elif module.score:
                sumbission_msg = "{0:.0f}%".format(module.score)
            else:
                not_graded = True

    for chapter in courseware_summary:
        if not chapter["display_name"] == "hidden":
            for section in chapter["sections"]:
                if section.graded and not check_sga_in_subsection(
                    section.location, staff_user
                ):
                    if not section._should_persist_per_attempted():
                        not_attempted = True

    if not_attempted:
        return "I"
    elif not_graded:
        return "C"
    else:
        return None
