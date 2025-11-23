# This file contains your existing BlogSerializer, CommentSerializer, etc.
# We're just organizing them in the new structure
from rest_framework import serializers
from blog.models import BaseBlogModel, Comment, UserSharedBlog
from users.models import UserTree, Milestone
from geographies.models.geos import Village, Subdistrict, District, State, Country
from django.apps import apps
import django.db.models as django_models
import uuid
from users.profilepic_manager.utils import get_profilepic_url



class CommentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    profile_pic = serializers.SerializerMethodField()

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        return get_profilepic_url(obj, request)

class CommentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user = CommentUserSerializer()
    text = serializers.CharField()
    likes = serializers.ListField(child=serializers.IntegerField())
    dislikes = serializers.ListField(child=serializers.IntegerField())
    created_at = serializers.DateTimeField()
    replies = serializers.ListField(child=serializers.DictField(), required=False)

    def to_representation(self, instance):
        """
        Convert Comment model instance -> dict for API response.
        """
        request = self.context.get('request')
        
        # Get user object
        try:
            user = UserTree.objects.get(id=instance.user_id)
        except UserTree.DoesNotExist:
            user = None
        
        # Use the CommentUserSerializer to ensure consistent profile pic formatting
        user_serializer = CommentUserSerializer(
            user, 
            context={'request': request}
        ) if user else None
        
        user_data = user_serializer.data if user_serializer else {
            "id": str(instance.user_id),
            "name": "Unknown User",
            "profile_pic": None
        }

        return {
            "id": str(instance.id),
            "user": user_data,
            "text": instance.text,
            "likes": instance.likes or [],
            "dislikes": instance.dislikes or [],
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "replies": getattr(instance, 'replies', []),  # Use the replies added in the view
        }

class BlogUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    profile_pic = serializers.SerializerMethodField()

    def get_profile_pic(self, obj):
        request = self.context.get('request')
        if request is None:
            return f"http://127.0.0.1:8000{obj.profilepic.url}"
        if getattr(obj, 'profilepic', None):
            return request.build_absolute_uri(obj.profilepic.url)
        return None

class BlogHeaderSerializer(serializers.Serializer):
    type = serializers.CharField()
    created_at = serializers.DateTimeField()
    user = BlogUserSerializer(source='*')
    narrative = serializers.CharField(required=False, allow_null=True)
    is_shared = serializers.BooleanField(default=False)
    shared_by_user_id = serializers.IntegerField(required=False, allow_null=True)
    shared_at = serializers.DateTimeField(required=False, allow_null=True)

class BlogBodySerializer(serializers.Serializer):
    body_text = serializers.CharField(allow_null=True, source='content')
    body_type_fields = serializers.DictField()

class BlogFooterSerializer(serializers.Serializer):
    likes = serializers.ListField(child=serializers.IntegerField())
    relevant_count = serializers.ListField(child=serializers.IntegerField())
    irrelevant_count = serializers.ListField(child=serializers.IntegerField())
    shares = serializers.ListField(child=serializers.IntegerField())
    comments = serializers.ListField(child=serializers.CharField())
    has_liked = serializers.BooleanField()
    has_shared = serializers.BooleanField()

class BlogSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    header = BlogHeaderSerializer(source='*')
    body = BlogBodySerializer(source='*')
    footer = BlogFooterSerializer(source='*')
    comments = CommentSerializer(many=True, required=False)

    def get_location_hierarchy(self, entity, level):
        """Build location hierarchy string based on geographical level"""
        location_parts = []

        if not entity:
            return "Unknown Location"

        try:
            if level == 'village':
                location_parts.append(entity.name)
                if getattr(entity, 'subdistrict', None):
                    location_parts.append(entity.subdistrict.name)
                    if getattr(entity.subdistrict, 'district', None):
                        location_parts.append(entity.subdistrict.district.name)
                        if getattr(entity.subdistrict.district, 'state', None):
                            location_parts.append(entity.subdistrict.district.state.name)
                            if getattr(entity.subdistrict.district.state, 'country', None):
                                location_parts.append(entity.subdistrict.district.state.country.name)

            elif level == 'subdistrict':
                location_parts.append(entity.name)
                if getattr(entity, 'district', None):
                    location_parts.append(entity.district.name)
                    if getattr(entity.district, 'state', None):
                        location_parts.append(entity.district.state.name)
                        if getattr(entity.district.state, 'country', None):
                            location_parts.append(entity.district.state.country.name)

            elif level == 'district':
                location_parts.append(entity.name)
                if getattr(entity, 'state', None):
                    location_parts.append(entity.state.name)
                    if getattr(entity.state, 'country', None):
                        location_parts.append(entity.state.country.name)

            elif level == 'state':
                location_parts.append(entity.name)
                if getattr(entity, 'country', None):
                    location_parts.append(entity.country.name)

            elif level == 'country':
                location_parts.append(entity.name)

        except Exception:
            return "Unknown Location"

        return ", ".join(location_parts) if location_parts else "Unknown Location"

    def get_formatted_date(self, report_instance, time_type):
        """Format date based on time type"""
        if not report_instance:
            return ""

        if time_type == 'daily' and hasattr(report_instance, 'date'):
            return getattr(report_instance, 'date').strftime('%Y-%m-%d')
        elif time_type == 'weekly' and hasattr(report_instance, 'week_start_date'):
            return f"Week {getattr(report_instance, 'week_number', '')}, {getattr(report_instance, 'year', '')}"
        elif time_type == 'monthly' and hasattr(report_instance, 'month'):
            month_name = report_instance.last_date.strftime('%B') if hasattr(report_instance, 'last_date') else ""
            return f"{month_name} {getattr(report_instance, 'year', '')}"
        return ""

    def _find_model_by_name(self, model_name):
        found = []
        for m in apps.get_models():
            if m.__name__ == model_name:
                found.append(m)

        if not found:
            return None, f"No model named '{model_name}' found in installed apps."

        for pref in ('report', 'activity_reports'):
            for m in found:
                if m._meta.app_label == pref:
                    return m, None

        return found[0], None

    def _resolve_report_model(self, report_type):
        if not report_type:
            return None, "report_type is empty"

        try:
            app_label, model_name = report_type.split('.', 1)
        except ValueError:
            return None, f"invalid report_type format: '{report_type}'"

        try:
            model = apps.get_model(app_label, model_name)
            if model:
                return model, None
        except LookupError:
            pass

        for fallback_app in ('report', 'activity_reports'):
            try:
                model = apps.get_model(fallback_app, model_name)
                if model:
                    return model, None
            except LookupError:
                continue

        return self._find_model_by_name(model_name)

    def get_deepest_location_id(self, concrete_blog):
        """
        Return the ID of the most specific populated geographic field available.
        Checks in order: village, subdistrict, district, state, country.
        """
        for level in ['village', 'subdistrict', 'district', 'state', 'country']:
            entity = getattr(concrete_blog, level, None)
            if entity:
                try:
                    return entity.id
                except AttributeError:
                    return entity  # fallback if not object with id attribute
        return None

    def to_representation(self, instance):
        base_blog = instance['base']
        concrete_blog = instance['concrete']
        blog_type = instance['type']
        comments = instance.get('comments', [])
        is_shared = instance.get('is_shared', False)
        shared_by_user_id = instance.get('shared_by_user_id')
        shared_at = instance.get('shared_at')

        user_data = BlogUserSerializer(instance['author'], context=self.context).data
        user_data['relation'] = instance['relation']

        header_data = {
            'type': blog_type,
            'created_at': base_blog.created_at,
            'user': user_data,
            'is_shared': is_shared,
            'shared_by_user_id': shared_by_user_id,
            'shared_at': shared_at
        }

        body_text = getattr(concrete_blog, 'content', None)
        body_type_fields = {}

        if blog_type in ['journey', 'successful_experience', 'milestone']:
            target_user_id = getattr(concrete_blog, 'target_user', None)
            if target_user_id:
                if target_user_id == instance['author'].id:
                    if blog_type == 'milestone':
                        header_data['narrative'] = 'On receiving their milestone'
                    else:
                        header_data['narrative'] = 'Writing on their own journey'
                else:
                    try:
                        target_user = UserTree.objects.get(id=target_user_id)
                        target_user_data = BlogUserSerializer(target_user, context=self.context).data
                        request = self.context.get('request')
                        if request and request.user.id == target_user_id:
                            target_relation = 'Your blog'
                        else:
                            from users.models import Circle
                            circle = Circle.objects.filter(
                                userid=request.user.id,
                                otherperson=target_user_id
                            ).first()
                            target_relation = circle.onlinerelation.replace('_', ' ').title() if circle and circle.onlinerelation else "Connection"

                        target_user_data['relation'] = target_relation
                        body_type_fields['target_user'] = target_user_data

                        if blog_type == 'milestone':
                            header_data['narrative'] = f'On receiving the milestone of {target_user.name}'
                        else:
                            header_data['narrative'] = f'Writing on the journey of {target_user.name}'
                    except UserTree.DoesNotExist:
                        body_type_fields['target_user'] = {'id': target_user_id, 'name': 'Unknown User'}
                        if blog_type == 'milestone':
                            header_data['narrative'] = 'On receiving someone\'s milestone'
                        else:
                            header_data['narrative'] = 'Writing on someone\'s journey'

        if blog_type == 'milestone':
            milestone_id = getattr(concrete_blog, 'milestone_id', None)
            if milestone_id:
                try:
                    milestone = Milestone.objects.get(id=milestone_id)
                    photo_url = None
                    if getattr(milestone, 'type', None) and getattr(milestone, 'photo_id', None):
                        photo_url = f"http://localhost:3000/{milestone.type}/{milestone.photo_id}.jpg"

                    body_type_fields['milestone'] = {
                        'id': str(milestone.id),
                        'title': milestone.title,
                        'text': milestone.text,
                        'photo_url': photo_url,
                        'type': milestone.type,
                        'photo_id': milestone.photo_id,
                    }
                except Milestone.DoesNotExist:
                    body_type_fields['milestone'] = None

        elif blog_type == 'report_insight':
            report_type = getattr(concrete_blog, 'report_type', None)
            report_id = getattr(concrete_blog, 'report_id', None)
            if not report_type or not report_id:
                body_type_fields['report_type'] = report_type
                body_type_fields['report_id'] = str(report_id) if report_id else None
                body_type_fields['report_error'] = "missing report_type or report_id"
            else:
                model, err = self._resolve_report_model(report_type)
                if err or model is None:
                    body_type_fields['report_type'] = report_type
                    body_type_fields['report_id'] = str(report_id)
                    body_type_fields['report_error'] = err
                else:
                    try:
                        lookup_id = report_id
                        if not isinstance(lookup_id, uuid.UUID):
                            try:
                                lookup_id = uuid.UUID(str(report_id))
                            except Exception:
                                lookup_id = str(report_id)

                        report_instance = model.objects.filter(id=lookup_id).first()
                        if not report_instance:
                            body_type_fields['report_type'] = report_type
                            body_type_fields['report_id'] = str(report_id)
                            body_type_fields['report_error'] = f"No {model._meta.app_label}.{model.__name__} with id={report_id}"
                        else:
                            model_name = model.__name__ or ""
                            mn_lower = model_name.lower()
                            if 'daily' in mn_lower:
                                time_type = 'daily'
                            elif 'weekly' in mn_lower:
                                time_type = 'weekly'
                            elif 'monthly' in mn_lower:
                                time_type = 'monthly'
                            else:
                                rt_lower = report_type.lower()
                                if 'daily' in rt_lower:
                                    time_type = 'daily'
                                elif 'weekly' in rt_lower:
                                    time_type = 'weekly'
                                elif 'monthly' in rt_lower:
                                    time_type = 'monthly'
                                else:
                                    time_type = 'unknown'

                            geographical_entity = None
                            level = None
                            for field in report_instance._meta.fields:
                                if isinstance(field, django_models.ForeignKey):
                                    related_model = getattr(field, 'related_model', None)
                                    if related_model in [Village, Subdistrict, District, State, Country]:
                                        geographical_entity = getattr(report_instance, field.name)
                                        level = field.name
                                        break

                            new_users = None
                            for attr in ('new_users', 'active_users', 'new_users_count', 'users_count'):
                                if hasattr(report_instance, attr):
                                    try:
                                        new_users = getattr(report_instance, attr)
                                    except Exception:
                                        new_users = 0
                                    break
                            if new_users is None:
                                new_users = 0

                            location = self.get_location_hierarchy(geographical_entity, level)
                            date = self.get_formatted_date(report_instance, time_type)

                            body_type_fields['report_kind'] = 'activity_report' if 'activity' in model._meta.app_label.lower() else 'report'
                            body_type_fields['time_type'] = time_type
                            body_type_fields['id'] = str(report_id)
                            body_type_fields['level'] = level
                            body_type_fields['location'] = location
                            body_type_fields['new_users'] = new_users
                            body_type_fields['date'] = date
                    except Exception as e:
                        body_type_fields['report_type'] = report_type
                        body_type_fields['report_id'] = str(report_id)
                        body_type_fields['report_error'] = str(e)

        elif blog_type == 'consumption':
            body_type_fields['url'] = getattr(concrete_blog, 'url', None)
            body_type_fields['contribution'] = getattr(concrete_blog, 'contribution', None)
            contribution_id = getattr(concrete_blog, 'contribution', None)
            if contribution_id:
                try:
                    from blog_related.models import Contribution  # adjust import if needed
                    contribution_obj = Contribution.objects.filter(id=contribution_id).first()
                    if contribution_obj:
                        
                        body_type_fields['title'] = contribution_obj.title
                except Exception:
                    body_type_fields['contribution'] = contribution_id

        elif blog_type == 'answering_question':
            question_id = getattr(concrete_blog, 'questionid', None)
            question_data = None
            if question_id:
                try:
                    from blog_related.models import Question  # adjust import if needed
                    question_obj = Question.objects.filter(id=question_id).first()
                    if question_obj:
                        question_data = {
                            'id': question_obj.id,
                            'text': question_obj.text,
                            'rank': question_obj.rank
                        }
                    else:
                        question_data = {
                            'id': question_id,
                            'text': None,
                            'rank': None
                        }
                except Exception:
                    question_data = {
                        'id': question_id,
                        'text': None,
                        'rank': None
                    }
            else:
                question_data = None
            body_type_fields['question'] = question_data

        elif blog_type == 'failed_initiation':
            # Find the deepest populated geo entity and its level name
            geo_entity = None
            level = None
            for lvl in ['village', 'subdistrict', 'district', 'state', 'country']:
                ent = getattr(concrete_blog, lvl, None)
                if ent:
                    geo_entity = ent
                    level = lvl
                    break  # stop at first found in priority order

            # Get the location string using existing method
            location = self.get_location_hierarchy(geo_entity, level)

            # Add location string to response
            body_type_fields['location'] = location

            # Also send other failed_initiation details
            body_type_fields['target_details'] = getattr(concrete_blog, 'target_details', None)
            body_type_fields['failure_reason'] = getattr(concrete_blog, 'failure_reason', None)

        footer_data = {
            'likes': base_blog.likes,
            'relevant_count': base_blog.relevant_count,
            'irrelevant_count': base_blog.irrelevant_count,
            'shares': base_blog.shares,
            'comments': base_blog.comments,
            'has_liked': instance['has_liked'],
            'has_shared': instance['has_shared']
        }

        return {
            'id': base_blog.id,
            'header': header_data,
            'body': {
                'body_text': body_text,
                'body_type_fields': body_type_fields
            },
            'footer': footer_data,
            'comments': comments  # Include comments in the response
        }