from django.urls import path
from .registration.views import PendingUserCreateView
from .registration.validations.views import ValidateInitiatorAPIView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('pending-user/create/', PendingUserCreateView.as_view(), name='pending_user_create'),
    path('pending-user/validate-initiator/', ValidateInitiatorAPIView.as_view(), name='validate_initiator'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
