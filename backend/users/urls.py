from django.urls import path
from .login.views import LoginWithGoogle
from .logout.views import LogoutView
from .makingconnections.views import CreateConnectionNotification
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .login.loginpushnotification_api import LoginPushNotificationAPIView
from .timeline.views import TimelineHeadView, TimelineTailView
from .milestones.views import UserMilestonesAPIView
from .login.TestCookieView import TestCookieView
from users.login.CookieTokenRefreshView import CookieTokenRefreshView
from .profile.views import UserProfileAPIView


urlpatterns = [
    path('auth/google/', LoginWithGoogle.as_view(), name='login_with_google'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('connections/create/', CreateConnectionNotification.as_view(), name='create_connection_notification'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('push-notification/login/', LoginPushNotificationAPIView.as_view(), name='login_push_notification'),
    path('timeline/<int:user_id>/', TimelineHeadView.as_view(), name='timeline_view'),
    path('timeline/tail/<int:user_id>/', TimelineTailView.as_view(), name='timeline_tail_view'),
    path('milestones/', UserMilestonesAPIView.as_view(), name='user_milestones'),
    path('test-cookie/', TestCookieView.as_view(), name='test_cookie_authentication'),
    path('token/refresh-cookie/', CookieTokenRefreshView.as_view(), name='cookie_token_refresh'),
    path('profile/<int:user_id>/', UserProfileAPIView.as_view(), name='user_profile'),
    
]
