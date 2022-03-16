"""
Helpers for instructor app.
"""
import logging

from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.module_render import get_module
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)

class DummyRequest:
    """Dummy request"""

    META = {}

    def __init__(self):  # lint-amnesty, pylint: disable=useless-return
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, usage_key, request=None, course=None):
    """Return the module for the (student, location) using a DummyRequest."""
    if request is None:
        request = DummyRequest()
        request.user = student

    descriptor = modulestore().get_item(usage_key, depth=0)
    field_data_cache = FieldDataCache([descriptor], usage_key.course_key, student)
    return get_module(student, request, usage_key, field_data_cache, course=course)


def check_sga_in_subsection(subsection_usage_key, user):
    """
    Check is there any sga block in given subsection
    """
    from lms.djangoapps.course_blocks.api import get_course_blocks

    try:
        subsection_structure = get_course_blocks(user, subsection_usage_key)
        if any(subsection_structure):
            for block in subsection_structure:
                if block.block_type == "edx_sga":
                    return True
                    break
            else:
                return False
        else:
            return False
    except Exception as err:
        log.info(str(err))
        return False
