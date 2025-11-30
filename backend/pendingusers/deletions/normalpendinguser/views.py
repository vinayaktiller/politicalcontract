from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
import json
import logging

from pendingusers.models import PendingUser, InitiationNotification

logger = logging.getLogger(__name__)

@require_http_methods(["DELETE"])
@csrf_exempt
def delete_pending_user_by_email(request):
    """
    Delete PendingUser and related InitiationNotification by email from request payload
    """
    try:
        # Parse JSON data from request body
        if request.body:
            try:
                data = json.loads(request.body)
                email = data.get('email')
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON in request body'
                }, status=400)
        else:
            return JsonResponse({
                'success': False,
                'error': 'No data provided in request body'
            }, status=400)
        
        # Check if email is provided
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email is required in the request payload'
            }, status=400)
        
        with transaction.atomic():
            # Get the PendingUser instance
            pending_user = get_object_or_404(PendingUser, gmail=email)
            
            # Get all related InitiationNotification instances
            notifications = InitiationNotification.objects.filter(applicant=pending_user)
            
            # Delete notifications first (due to foreign key constraints)
            notifications_count = notifications.count()
            notifications.delete()
            
            # Delete the pending user
            pending_user.delete()
            
            logger.info(f"Successfully deleted PendingUser '{email}' and {notifications_count} related notifications")
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted user {email} and {notifications_count} related notifications',
                'deleted_email': email,
                'notifications_deleted': notifications_count
            })
            
    except PendingUser.DoesNotExist:
        logger.warning(f"PendingUser with email '{email}' not found")
        return JsonResponse({
            'success': False,
            'error': f'User with email {email} not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error deleting user {email}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Failed to delete user: {str(e)}'
        }, status=500)