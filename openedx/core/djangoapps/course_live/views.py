"""
View for course live app
"""
from typing import Dict

import edx_api_doc_tools as apidocs
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from lti_consumer.api import get_lti_pii_sharing_state_for_course
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from common.djangoapps.util.views import ensure_valid_course_key
from openedx.core.djangoapps.course_live.permissions import IsStaffOrInstructor
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from ...lib.api.view_utils import verify_course_exists
from .models import AVAILABLE_PROVIDERS, CourseLiveConfiguration
from .serializers import CourseLiveConfigurationSerializer


class CourseLiveConfigurationView(APIView):
    """
    View for configuring CourseLive settings.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaffOrInstructor,)

    @apidocs.schema(
        parameters=[
            apidocs.path_parameter(
                'course_id',
                str,
                description="The course for which to get provider list",
            )
        ],
        responses={
            200: CourseLiveConfigurationSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @ensure_valid_course_key
    @verify_course_exists()
    def get(self, request: Request, course_id: str) -> Response:
        """
        Handle HTTP/GET requests
        """
        pii_sharing_allowed = get_lti_pii_sharing_state_for_course(course_id)
        if not pii_sharing_allowed:
            return Response({
                "pii_sharing_allowed": pii_sharing_allowed,
                "message": "PII sharing is not allowed on this course"
            })

        configuration = CourseLiveConfiguration.get(course_id)
        serializer = CourseLiveConfigurationSerializer(configuration, context={
            "pii_sharing_allowed": pii_sharing_allowed,
        })

        return Response(serializer.data)

    @apidocs.schema(
        parameters=[
            apidocs.path_parameter(
                'course_id',
                str,
                description="The course for which to get provider list",
            ),
            apidocs.path_parameter(
                'lti_1p1_client_key',
                str,
                description="The LTI provider's client key",
            ),
            apidocs.path_parameter(
                'lti_1p1_client_secret',
                str,
                description="The LTI provider's client secretL",
            ),
            apidocs.path_parameter(
                'lti_1p1_launch_url',
                str,
                description="The LTI provider's launch URL",
            ),
            apidocs.path_parameter(
                'provider_type',
                str,
                description="The LTI provider's launch URL",
            ),
            apidocs.parameter(
                'lti_config',
                apidocs.ParameterLocation.QUERY,
                object,
                description="The lti_config object with required additional parameters ",
            ),
        ],
        responses={
            200: CourseLiveConfigurationSerializer,
            400: "Required parameters are missing.",
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @ensure_valid_course_key
    @verify_course_exists()
    def post(self, request, course_id: str) -> Response:
        """
        Handle HTTP/POST requests
        """
        pii_sharing_allowed = get_lti_pii_sharing_state_for_course(course_id)
        if not pii_sharing_allowed:
            return Response({
                "pii_sharing_allowed": pii_sharing_allowed,
                "message": "PII sharing is not allowed on this course"
            })

        configuration = CourseLiveConfiguration.get(course_id)
        serializer = CourseLiveConfigurationSerializer(
            configuration,
            data=request.data,
            context={
                "pii_sharing_allowed": pii_sharing_allowed,
                "course_id": course_id
            }
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)
        serializer.save()
        return Response(serializer.data)


class CourseLiveProvidersView(APIView):
    """
    Read only view that lists details of LIVE providers available for a course.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaffOrInstructor,)

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'course_id',
                apidocs.ParameterLocation.PATH,
                description="The course for which to get provider list",
            )
        ],
        responses={
            200: CourseLiveConfigurationSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @ensure_valid_course_key
    @verify_course_exists()
    def get(self, request, course_id: str, **_kwargs) -> Response:
        """
        Handle HTTP/GET requests
        """
        data = self.get_provider_data(course_id)
        return Response(data)

    @staticmethod
    def get_provider_data(course_id: str) -> Dict:
        """
        Get provider data for specified course
        Args:
            course_id (str): course key string

        Returns:
            Dict: course Live providers
        """
        configuration = CourseLiveConfiguration.get(course_id)
        return {
            "providers": {
                "active": configuration.provider_type if configuration else "",
                "available": AVAILABLE_PROVIDERS
            }
        }
