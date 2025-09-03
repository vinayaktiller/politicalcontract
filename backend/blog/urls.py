# urls.py
from django.urls import path
from .Journeyblog.views import JourneyBlogAPIView
from .posting_blogs.views import BlogCreateAPIView
from .circleconcontacts.views import CircleContactsView
from .blogpage.views import (
    CircleBlogsView, LikeBlogView, ShareBlogView, 
    BlogDetailView, CommentView, CommentDetailView, ReplyView, CommentLikeView
)

urlpatterns = [
    path('journey-blogs/', JourneyBlogAPIView.as_view(), name='journey-blog-list'),
    path('journey-blogs/<uuid:pk>/', JourneyBlogAPIView.as_view(), name='journey-blog-detail'),
    path('create-blog/', BlogCreateAPIView.as_view(), name='create-blog'),
    path('circle-contacts/', CircleContactsView.as_view(), name='circle-contacts'),
    path('circle-blogs/', CircleBlogsView.as_view(), name='circle-blogs'),
    path('blogs/<uuid:blog_id>/like/', LikeBlogView.as_view(), name='like-blog'),
    path('blogs/<uuid:blog_id>/share/', ShareBlogView.as_view(), name='share-blog'),
    path('blogs/<uuid:blog_id>/', BlogDetailView.as_view(), name='blog-detail'),
    path('blogs/<uuid:blog_id>/comments/', CommentView.as_view(), name='blog-comments'),
    path('comments/<uuid:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
    path('comments/<uuid:comment_id>/like/', CommentLikeView.as_view(), name='comment-like'),
    path('comments/<uuid:comment_id>/reply/', ReplyView.as_view(), name='comment-reply'),
]