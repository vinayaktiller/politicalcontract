from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Petitioner, UserTree, Circle, Milestone
from event.models import Group
from activity_reports.models import UserMonthlyActivity
from .serializers import UserSerializer, MilestoneSerializer, GroupSerializer, ProfileSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta


class UserProfileAPIView(APIView):

    def get(self, request, user_id):
        user = get_object_or_404(Petitioner, id=user_id)
        user_tree = UserTree.objects.filter(id=user_id).first()
        circles = Circle.objects.filter(userid=user_id)
        milestones = Milestone.objects.filter(user_id=user_id).order_by('-created_at')
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_activity = UserMonthlyActivity.objects.filter(
            user=user, year=current_year, month=current_month
        ).first()

        founded_groups = Group.objects.filter(founder=user_id)
        speaking_groups = Group.objects.filter(speakers__contains=[user_id])

        streak = self.calculate_activity_streak(user_id)
        profile_description = self.generate_profile_description(
            user, user_tree, circles, milestones, monthly_activity,
            founded_groups, speaking_groups, streak
        )

        user_data = UserSerializer(user, context={'request': request}).data
        milestones_data = MilestoneSerializer(milestones, many=True).data
        founded_groups_data = GroupSerializer(founded_groups, many=True, context={'request': request}).data
        speaking_groups_data = GroupSerializer(speaking_groups, many=True, context={'request': request}).data
        user_tree_data = ProfileSerializer(user_tree, context={'request': request}).data if user_tree else None

        return Response({
            'user': user_data,
            'user_tree': user_tree_data,
            'profile_description': profile_description,
            'milestones': milestones_data,
            'founded_groups': founded_groups_data,
            'speaking_groups': speaking_groups_data,
            'streak': streak,
        }, status=status.HTTP_200_OK)

    def calculate_activity_streak(self, user_id):
        today = timezone.now().date()
        streak = 0
        for i in range(30):
            check_date = today - timedelta(days=i)
            activity = UserMonthlyActivity.objects.filter(
                user_id=user_id,
                year=check_date.year,
                month=check_date.month,
                active_days__contains=[check_date.day]
            ).exists()
            if activity:
                streak += 1
            else:
                break
        return streak

    def generate_profile_description(
            self, user, user_tree, circles, milestones, monthly_activity,
            founded_groups, speaking_groups, streak):
        description_parts = []

        location_parts = []
        if user.village: location_parts.append(user.village.name)
        if user.subdistrict: location_parts.append(user.subdistrict.name)
        if user.district: location_parts.append(user.district.name)
        if user.state: location_parts.append(user.state.name)
        if user.country: location_parts.append(user.country.name)

        location_str = ", ".join(location_parts) if location_parts else "an unknown location"

        description_parts.append(
            f"{user.first_name} {user.last_name} is a {user.age}-year-old {user.get_gender_display().lower()} "
            f"from {location_str} who joined on {user.date_joined.strftime('%B %d, %Y')}."
        )

        if user_tree:
            if user_tree.childcount > 0:
                description_parts.append(
                    f"As an initiator, {user.first_name} has directly brought {user_tree.childcount} members "
                    f"into the movement, creating a ripple effect that extends to {user_tree.influence} people "
                    f"in their network."
                )

            initiation_milestones = [m for m in milestones if m.type == 'initiation']
            influence_milestones = [m for m in milestones if m.type == 'influence']

            if initiation_milestones:
                latest_initiation = initiation_milestones[0]
                description_parts.append(
                    f"For their initiation efforts, {user.first_name} has achieved the title of "
                    f"'{latest_initiation.title}' - {latest_initiation.text}"
                )

            if influence_milestones:
                latest_influence = influence_milestones[0]
                description_parts.append(
                    f"In terms of influence, they've been recognized as a '{latest_influence.title}' - "
                    f"{latest_influence.text}"
                )

        if monthly_activity:
            active_days = len(monthly_activity.active_days)
            description_parts.append(
                f"This month, {user.first_name} has shown support on {active_days} days, "
                f"maintaining a streak of {streak} consecutive days of activity."
            )

        if founded_groups or speaking_groups:
            group_roles = []
            if founded_groups:
                group_roles.append(f"founder of {founded_groups.count()} groups")
            if speaking_groups:
                group_roles.append(f"speaker in {speaking_groups.count()} groups")

            description_parts.append(
                f"{user.first_name} actively contributes to the community as the {', and '.join(group_roles)}."
            )

        relation_counts = {}
        for circle in circles:
            relation_type = circle.onlinerelation
            relation_counts[relation_type] = relation_counts.get(relation_type, 0) + 1

        if relation_counts:
            relations_text = []
            for rel_type, count in relation_counts.items():
                readable_type = dict(Circle.ONLINE_RELATION_CHOICES).get(rel_type, rel_type)
                relations_text.append(f"{count} {readable_type.lower()}")

            description_parts.append(
                f"In their network, {user.first_name} is connected to {', '.join(relations_text)}."
            )

        return " ".join(description_parts)
