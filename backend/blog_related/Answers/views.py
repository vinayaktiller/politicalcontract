from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import connection
from users.login.authentication import CookieJWTAuthentication

from users.models import Circle, UserTree
from blog.models import BaseBlogModel, Comment
from blog.blogpage.serializers import BlogSerializer, CommentSerializer

class QuestionAnswersView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id):
        user = request.user

        # 1. Get all 'answering_question_*' base blogs ordered by created_at
        base_blogs = BaseBlogModel.objects.filter(
            Q(type='answering_question_micro') |
            Q(type='answering_question_short_essay') |
            Q(type='answering_question_article')
        ).order_by('-created_at')

        # 2. Filter for blogs answering the given question_id
        valid_ids = []
        for blog in base_blogs:
            # blog.type format: 'answering_question_micro' etc
            base_type = 'answering_question'
            content_type = blog.type.split('_')[-1]
            concrete_blog = self.get_concrete_blog(blog.id, base_type, content_type)
            if concrete_blog and getattr(concrete_blog, 'questionid', None) == int(question_id):
                valid_ids.append(blog.id)

        # 3. Narrow down to valid base blogs
        filtered_base_blogs = BaseBlogModel.objects.filter(id__in=valid_ids).order_by('-created_at')

        # Prefetch users for all authors
        userids = {b.userid for b in filtered_base_blogs if b.userid is not None}
        users = UserTree.objects.filter(id__in=userids)
        user_map = {u.id: u for u in users}

        # Prefetch circles for relation mapping
        circles = Circle.objects.filter(userid=user.id)
        circle_map = {circle.otherperson: circle for circle in circles}

        # 4. Prefetch all comments IDs using recursive SQL from all blogs
        all_comment_ids = set()
        for blog in filtered_base_blogs:
            all_comment_ids.update(blog.comments)
            if blog.comments:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        WITH RECURSIVE comment_tree AS (
                            SELECT id, parent
                            FROM blog.comment
                            WHERE id = ANY(%s)
                            UNION ALL
                            SELECT c.id, c.parent
                            FROM blog.comment c
                            INNER JOIN comment_tree ct ON c.parent = ct.id AND c.parent_type = 'comment'
                        )
                        SELECT id FROM comment_tree;
                    """, [blog.comments])
                    rows = cursor.fetchall()
                    for row in rows:
                        all_comment_ids.add(row)

        all_comments = Comment.objects.filter(id__in=all_comment_ids).order_by('created_at')

        # Build comments by parent mapping
        comments_by_parent = {}
        for comment in all_comments:
            if comment.parent not in comments_by_parent:
                comments_by_parent[comment.parent] = []
            comments_by_parent[comment.parent].append(comment)

        # Prefetch users for comments
        comment_user_ids = {comment.user_id for comment in all_comments}
        comment_users = UserTree.objects.filter(id__in=comment_user_ids)
        comment_user_map = {u.id: u for u in comment_users}

        blog_data = []
        concrete_skip_count = 0
        author_skip_count = 0
        valid_content_types = {'micro', 'short_essay', 'article'}

        for base_blog in filtered_base_blogs:
            blog_type_raw = base_blog.type
            if not blog_type_raw:
                continue
            content_type = None
            blog_type = blog_type_raw
            for ct in valid_content_types:
                if blog_type_raw.endswith('_' + ct):
                    blog_type = blog_type_raw[:-len(ct)-1]
                    content_type = ct
                    break

            # Only use 'answering_question' as base for this endpoint
            concrete_blog = self.get_concrete_blog(base_blog.id, 'answering_question', content_type)
            if not concrete_blog:
                concrete_skip_count += 1
                continue
            author = user_map.get(base_blog.userid)
            if not author:
                author_skip_count += 1
                continue
            # Map relation using circles
            if base_blog.userid == user.id:
                relation = 'Your blog'
            else:
                circle = circle_map.get(base_blog.userid)
                relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"
            has_liked = user.id in base_blog.likes
            has_shared = user.id in base_blog.shares
            blog_comments = self.build_comment_hierarchy_with_serializer(
                base_blog.id, comments_by_parent, comment_user_map, request
            )
            blog_data.append({
                'base': base_blog,
                'concrete': concrete_blog,
                'type': blog_type,
                'content_type': content_type,
                'author': author,
                'relation': relation,
                'has_liked': has_liked,
                'has_shared': has_shared,
                'comments': blog_comments
            })

        print(f"[QUESTION_ANSWERS] Sent {len(blog_data)} blogs")
        print(f"[QUESTION_ANSWERS] Skipped concrete: {concrete_skip_count}, skipped author: {author_skip_count}")

        serializer = BlogSerializer(blog_data, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def build_comment_hierarchy_with_serializer(self, blog_id, comments_by_parent, user_map, request):
        def build_tree(parent_id):
            comments = []
            if parent_id in comments_by_parent:
                for comment in comments_by_parent[parent_id]:
                    user = user_map.get(comment.user_id)
                    comment_serializer = CommentSerializer(
                        comment,
                        context={'request': request}
                    )
                    comment_data = comment_serializer.data
                    comment_data['replies'] = build_tree(comment.id)
                    comments.append(comment_data)
            return comments
        return build_tree(blog_id)

    def get_concrete_blog(self, blog_id, blog_type, content_type):
        # Only 'answering_question' blogs used here
        if blog_type == 'answering_question':
            from blog.models import (
                MicroAnsweringQuestionBlog, ShortEssayAnsweringQuestionBlog,
                ArticleAnsweringQuestionBlog
            )
            model_map = {
                'micro': MicroAnsweringQuestionBlog,
                'short_essay': ShortEssayAnsweringQuestionBlog,
                'article': ArticleAnsweringQuestionBlog
            }
        else:
            return None

        if not content_type or content_type not in model_map:
            return None
        try:
            return model_map[content_type].objects.get(id=blog_id)
        except model_map[content_type].DoesNotExist:
            return None
