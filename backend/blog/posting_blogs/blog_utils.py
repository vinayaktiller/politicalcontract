# blog_utils.py
from django.db import connection
from ..models import BaseBlogModel, Comment
from users.models import UserTree, Circle
from ..blogpage.serializers import BlogSerializer, CommentSerializer

class BlogDataBuilder:
    def __init__(self, user, request):
        self.user = user
        self.request = request

    def get_concrete_blog(self, blog_id, blog_type, content_type):
        # Import models locally to avoid circular imports
        if blog_type == 'journey':
            from ..models import (
                MicroJourneyBlog, ShortEssayJourneyBlog, ArticleJourneyBlog
            )
            model_map = {
                'micro': MicroJourneyBlog,
                'short_essay': ShortEssayJourneyBlog,
                'article': ArticleJourneyBlog
            }

        elif blog_type == 'milestone':
            from ..models import (
                MicroMilestoneJourneyBlog, ShortEssayMilestoneJourneyBlog,
                ArticleMilestoneJourneyBlog
            )
            model_map = {
                'micro': MicroMilestoneJourneyBlog,
                'short_essay': ShortEssayMilestoneJourneyBlog,
                'article': ArticleMilestoneJourneyBlog
            }

        elif blog_type == 'report_insight':
            from ..models import (
                report_insight_micro, report_insight_short_essay, report_insight_article
            )
            model_map = {
                'micro': report_insight_micro,
                'short_essay': report_insight_short_essay,
                'article': report_insight_article
            }

        elif blog_type == 'successful_experience':
            from ..models import (
                MicroSuccessfulExperience, ShortEssaySuccessfulExperience,
                ArticleSuccessfulExperience
            )
            model_map = {
                'micro': MicroSuccessfulExperience,
                'short_essay': ShortEssaySuccessfulExperience,
                'article': ArticleSuccessfulExperience
            }

        elif blog_type == 'answering_question':
            from ..models import (
                MicroAnsweringQuestionBlog, ShortEssayAnsweringQuestionBlog,
                ArticleAnsweringQuestionBlog
            )
            model_map = {
                'micro': MicroAnsweringQuestionBlog,
                'short_essay': ShortEssayAnsweringQuestionBlog,
                'article': ArticleAnsweringQuestionBlog
            }

        elif blog_type == 'consumption':
            from ..models import (
                MicroConsumption, ShortEssayConsumption, ArticleConsumption
            )
            model_map = {
                'micro': MicroConsumption,
                'short_essay': ShortEssayConsumption,
                'article': ArticleConsumption
            }

        elif blog_type == 'failed_initiation':
            from ..models import (
                MicroFailedInitiationExperience, ShortEssayFailedInitiationExperience,
                ArticleFailedInitiationExperience
            )
            model_map = {
                'micro': MicroFailedInitiationExperience,
                'short_essay': ShortEssayFailedInitiationExperience,
                'article': ArticleFailedInitiationExperience
            }
        else:
            return None

        if not content_type or content_type not in model_map:
            return None

        try:
            return model_map[content_type].objects.get(id=blog_id)
        except model_map[content_type].DoesNotExist:
            return None


    def build_comment_hierarchy(self, blog_id, comments_by_parent, user_map):
        """Build comment hierarchy using serializer"""
        def build_tree(parent_id):
            comments = []
            if parent_id in comments_by_parent:
                for comment in comments_by_parent[parent_id]:
                    user = user_map.get(comment.user_id)
                    
                    comment_serializer = CommentSerializer(
                        comment, 
                        context={'request': self.request}
                    )
                    
                    comment_data = comment_serializer.data
                    comment_data['replies'] = build_tree(comment.id)
                    comments.append(comment_data)
            return comments
        
        return build_tree(blog_id)

    def get_blog_data(self, base_blog):
        """Build complete blog data for a single blog"""
        # Get author
        try:
            author = UserTree.objects.get(id=base_blog.userid)
        except UserTree.DoesNotExist:
            return None

        # Get relation
        if base_blog.userid == self.user.id:
            relation = 'Your blog'
        else:
            circle = Circle.objects.filter(
                userid=self.user.id, 
                otherperson=base_blog.userid
            ).first()
            relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"

        # Check if current user has liked/shared
        has_liked = self.user.id in base_blog.likes
        has_shared = self.user.id in base_blog.shares

        # Get comments
        all_comment_ids = set(base_blog.comments)
        if base_blog.comments:
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
                """, [base_blog.comments])
                rows = cursor.fetchall()
                for row in rows:
                    all_comment_ids.add(row[0])

        # Prefetch comments
        all_comments = Comment.objects.filter(id__in=all_comment_ids).order_by('created_at')
        
        # Build comments map
        comments_by_parent = {}
        for comment in all_comments:
            if comment.parent not in comments_by_parent:
                comments_by_parent[comment.parent] = []
            comments_by_parent[comment.parent].append(comment)

        # Prefetch comment users
        comment_user_ids = {comment.user_id for comment in all_comments}
        comment_users = UserTree.objects.filter(id__in=comment_user_ids)
        comment_user_map = {u.id: u for u in comment_users}

        # Build comment hierarchy
        blog_comments = self.build_comment_hierarchy(
            base_blog.id, comments_by_parent, comment_user_map
        )

        # Get concrete blog
        blog_type_raw = base_blog.type
        if not blog_type_raw:
            return None

        if '_' in blog_type_raw:
            blog_type, content_type = blog_type_raw.rsplit('_', 1)
        else:
            blog_type = blog_type_raw
            content_type = None

        concrete_blog = self.get_concrete_blog(base_blog.id, blog_type, content_type)
        if not concrete_blog:
            return None

        return {
            'base': base_blog,
            'concrete': concrete_blog,
            'type': blog_type,
            'content_type': content_type,
            'author': author,
            'relation': relation,
            'has_liked': has_liked,
            'has_shared': has_shared,
            'comments': blog_comments
        }