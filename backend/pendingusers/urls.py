from django.urls import path
from .registration.views import PendingUserCreateView
from .registration.validations.views import ValidateInitiatorAPIView
from django.conf.urls.static import static
from django.conf import settings
from .Successful_experience.views import verify_user_response
from .no_initiator.phone_number_views import PhoneNumberAPIView
from .dashboard_for_no_intitators.views import PendingUserNoInitiatorListView, ClaimPendingUser, UnclaimPendingUser,  UpdatePendingUserNotes, MarkAsSpam
from .dashboard_for_no_intitators.VerifyPendingUser.views import VerifyPendingUser
from .dashboard_for_no_intitators.VerifyPendingUser.views import RejectPendingUser
from .deletions.normalpendinguser.views import delete_pending_user_by_email
# from .dashboard_for_no_intitators.VerifyPendingUser.views import AcceptRejectionCleanup

urlpatterns = [
    path('pending-user/create/', PendingUserCreateView.as_view(), name='pending_user_create'),
    path('pending-user/validate-initiator/', ValidateInitiatorAPIView.as_view(), name='validate_initiator'),
    path('successful-experience/verify-response/', verify_user_response, name='verify_user_response'),
    path('api/phone-number/', PhoneNumberAPIView.as_view(), name='phone-number-api'),
    path('admin/pending-users/no-initiator/', PendingUserNoInitiatorListView.as_view(), name='pending-users-no-initiator'),
    path('admin/pending-users/<int:user_id>/claim/', ClaimPendingUser.as_view(), name='claim-pending-user'),
    path('admin/pending-users/<int:user_id>/verify/', VerifyPendingUser.as_view(), name='verify-pending-user'),
    path('admin/pending-users/<int:user_id>/unclaim/', UnclaimPendingUser.as_view(), name='unclaim-pending-user'),
    path('admin/pending-users/<int:user_id>/notes/', UpdatePendingUserNotes.as_view(), name='update-pending-user-notes'),
    path('admin/pending-users/<int:user_id>/mark-spam/', MarkAsSpam.as_view(), name='mark-pending-user-spam'),
    path('admin/pending-users/<int:user_id>/reject/', RejectPendingUser.as_view(), name='reject-pending-user'),
    #
    path('pending-users/delete/', delete_pending_user_by_email, name='delete-pending-user-by-email'),  # Changed URL pattern
    # path('admin/pending-users/<int:user_id>/cleanup-rejection/', AcceptRejectionCleanup.as_view(), name='cleanup-rejection'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)