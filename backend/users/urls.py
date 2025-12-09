"""
URL configuration for the `users` app.

Defines endpoints related to authentication, tokens, timelines, milestones,
connections, push notifications, test utilities and user profiles.
"""

from django.urls import path
from .login.views import LoginWithGoogle
from .logout.views import LogoutView
from .makingconnections.views import CreateConnectionNotification
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView  # TokenVerifyView available if needed
from .login.loginpushnotification_api import LoginPushNotificationAPIView
from .timeline.views import TimelineHeadView, TimelineTailView
from .milestones.views import UserMilestonesAPIView, MarkMilestoneCompletedAPIView  # view to mark milestone completed
from .login.TestCookieView import TestCookieView
from users.login.CookieTokenRefreshView import CookieTokenRefreshView  # imported via package path
from .profile.views import UserProfileAPIView
from .landing.views import LandingPageAuth

urlpatterns = [
    # --- Authentication endpoints ---
    path('auth/google/', LoginWithGoogle.as_view(), name='login_with_google'),  # Google OAuth login
    path('auth/landing/', LandingPageAuth.as_view(), name='landing_page_auth'),  # landing page auth helper
    path('logout/', LogoutView.as_view(), name='logout'),

    # --- Connections / Notifications ---
    path('connections/create/', CreateConnectionNotification.as_view(), name='create_connection_notification'),

    # --- JWT token endpoints (simple-jwt) ---
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # obtain access + refresh tokens
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # refresh access token

    # --- Push notifications ---
    path('push-notification/login/', LoginPushNotificationAPIView.as_view(), name='login_push_notification'),

    # --- Timeline endpoints ---
    path('timeline/<int:user_id>/', TimelineHeadView.as_view(), name='timeline_view'),  # recent timeline entries
    path('timeline/tail/<int:user_id>/', TimelineTailView.as_view(), name='timeline_tail_view'),  # older/paginated entries

    # --- Milestones ---
    path('milestones/', UserMilestonesAPIView.as_view(), name='user_milestones'),  # list user milestones
    # path('milestones/over/', MarkMilestoneCompletedAPIView.as_view(), name='mark_milestone_completed'),  # mark milestone complete
    
    path('milestones/complete/', MarkMilestoneCompletedAPIView.as_view(), name='mark_milestone_completed'),  # mark milestone complete

    # --- Development / testing utilities ---
    path('test-cookie/', TestCookieView.as_view(), name='test_cookie_authentication'),  # verify cookie auth behavior
    path('token/refresh-cookie/', CookieTokenRefreshView.as_view(), name='cookie_token_refresh'),  # refresh via cookie (custom)

    # --- User profile ---
    path('profile/<int:user_id>/', UserProfileAPIView.as_view(), name='user_profile'),  # user profile view
]