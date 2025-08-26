from django.urls import path
from .registration.views import PendingUserCreateView
from .registration.validations.views import ValidateInitiatorAPIView
from django.conf.urls.static import static
from django.conf import settings
from .Successful_experience.views import verify_user_response

urlpatterns = [
    path('pending-user/create/', PendingUserCreateView.as_view(), name='pending_user_create'),
    path('pending-user/validate-initiator/', ValidateInitiatorAPIView.as_view(), name='validate_initiator'),
    path('successful-experience/verify-response/', verify_user_response, name='verify_user_response'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
