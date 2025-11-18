from django.urls import path
from .groups.group_registration.views import GroupRegistrationView
from .groups.group_validation.views import GroupValidationAPIView
from .groups.group_page_api.views import UserGroupsAPIView
from .groups.groups_list_page.views import UserGroupsAPI
from .groups.group_setup.views import GroupDetailView, VerifySpeakerView, AddPendingSpeakerView, UploadGroupProfilePictureView
from .groups.GroupDetailspage.views import GroupDetailpageView

urlpatterns = [
    path('register/', GroupRegistrationView.as_view(), name='group-register'),
    path('validate/', GroupValidationAPIView.as_view(), name='group-validate'),
    path('user-groups/', UserGroupsAPI.as_view(), name='user-groups'),
    path('group/<int:group_id>/', GroupDetailView.as_view(), name='group-detail'),
    path('group/<int:group_id>/verify-speaker/', VerifySpeakerView.as_view(), name='verify-speaker'),
    path('group/<int:group_id>/add-pending-speaker/', AddPendingSpeakerView.as_view(), name='add-pending-speaker'),
    path('group/<int:group_id>/upload-profile-picture/', UploadGroupProfilePictureView.as_view(), name='upload-group-profile-picture'),
    path('group/<int:group_id>/details/', GroupDetailpageView.as_view(), name='group-details'),
]