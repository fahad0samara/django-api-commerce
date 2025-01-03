from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.http import Http404

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, ValidationError):
            return Response(
                {'detail': exc.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, Http404):
            return Response(
                {'detail': 'Not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(
            {'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if response.status_code == 403:
        response.data = {
            'status_code': 403,
            'error': 'Forbidden',
            'message': response.data.get('detail', 'You do not have permission to perform this action.')
        }

    elif response.status_code == 401:
        response.data = {
            'status_code': 401,
            'error': 'Unauthorized',
            'message': response.data.get('detail', 'Authentication credentials were not provided.')
        }

    return response
