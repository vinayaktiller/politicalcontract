from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from users.models import Petitioner, UserTree, Circle, Milestone, ProfileCache
from event.models import Group
from activity_reports.models import UserMonthlyActivity

from .serializers import (
    UserSerializer,
    MilestoneSerializer,
    GroupSerializer,
    ProfileSerializer
)
#
#
#
#

class UserProfileAPIView(APIView):

    def get(self, request, user_id):
        user = get_object_or_404(Petitioner, id=user_id)
        today = timezone.now().date()

        # 1) Try existing cache
        cache = ProfileCache.objects.filter(user=user).first()

        if cache and cache.generated_at.date() == today:
            return Response(cache.profile_data, status=status.HTTP_200_OK)

        # 2) Generate fresh profile
        profile_data = self.generate_fresh_profile_data(user, request)

        # 3) Save/overwrite cache
        ProfileCache.objects.update_or_create(
            user=user,
            defaults={
                "profile_data": profile_data,
                "last_activity_check": timezone.now(),
                "is_stale": False
            }
        )

        return Response(profile_data, status=status.HTTP_200_OK)

    # ----------------------------------------------------------
    # FRESH PROFILE DATA (includes your new streak_data)
    # ----------------------------------------------------------

    def generate_fresh_profile_data(self, user, request=None):
        user_id = user.id

        user_tree = UserTree.objects.filter(id=user_id).first()
        circles = Circle.objects.filter(userid=user_id)
        milestones = Milestone.objects.filter(user_id=user_id).order_by("-created_at")

        now = timezone.now()
        monthly_activity = UserMonthlyActivity.objects.filter(
            user=user, year=now.year, month=now.month
        ).first()

        founded_groups = Group.objects.filter(founder=user_id)
        speaking_groups = Group.objects.filter(speakers__contains=[user_id])

        # ✔ Use your new advanced streak calculation
        streak_data = self.calculate_activity_streaks(user_id, user.date_joined.date())

        profile_description = self.generate_profile_description(
            user,
            user_tree,
            circles,
            milestones,
            monthly_activity,
            founded_groups,
            speaking_groups,
            streak_data
        )

        user_data = UserSerializer(user, context={"request": request}).data
        milestones_data = MilestoneSerializer(milestones, many=True).data
        founded_groups_data = GroupSerializer(founded_groups, many=True, context={"request": request}).data
        speaking_groups_data = GroupSerializer(speaking_groups, many=True, context={"request": request}).data
        user_tree_data = (
            ProfileSerializer(user_tree, context={"request": request}).data
            if user_tree else None
        )

        return {
            "user": user_data,
            "user_tree": user_tree_data,
            "profile_description": profile_description,
            "milestones": milestones_data,
            "founded_groups": founded_groups_data,
            "speaking_groups": speaking_groups_data,
            "streak_data": streak_data,
            "generated_at": timezone.now().isoformat(),
            "cache_type": "fresh",
        }

    # ----------------------------------------------------------
    # ADVANCED STREAK SYSTEM (your complete logic)
    # ----------------------------------------------------------

    def calculate_activity_streaks(self, user_id, join_date):
        today = timezone.now().date()
        join_date = min(join_date, today)

        streak_data = {
            "current_streak": 0,
            "last_10_days": 0,
            "last_30_days": 0,
            "last_100_days": 0,
            "total_active_days": 0,
            "join_date": join_date.isoformat(),  # Fixed: Convert to ISO string
            "days_since_join": (today - join_date).days,
        }

        streak_data["current_streak"] = self._calculate_current_streak(user_id, today)

        # last 10 days
        ten_days_ago = max(today - timedelta(days=9), join_date)
        streak_data["last_10_days"] = self._count_active_days_in_range(user_id, ten_days_ago, today)

        # last 30 days
        thirty_days_ago = max(today - timedelta(days=29), join_date)
        streak_data["last_30_days"] = self._count_active_days_in_range(user_id, thirty_days_ago, today)

        # last 100 days
        hundred_days_ago = max(today - timedelta(days=99), join_date)
        streak_data["last_100_days"] = self._count_active_days_in_range(user_id, hundred_days_ago, today)

        # total active days since join
        streak_data["total_active_days"] = self._count_active_days_in_range(user_id, join_date, today)

        return streak_data

    def _calculate_current_streak(self, user_id, today):
        streak = 0
        current_date = today

        for _ in range(365):  # max lookback
            activity = UserMonthlyActivity.objects.filter(
                user_id=user_id,
                year=current_date.year,
                month=current_date.month,
                active_days__contains=[current_date.day]
            ).exists()

            if not activity:
                break

            streak += 1
            current_date -= timedelta(days=1)

        return streak

    def _count_active_days_in_range(self, user_id, start_date, end_date):
        if start_date > end_date:
            return 0

        # Positions of months to inspect
        months_to_check = set()
        temp_date = start_date
        
        # Use first day of month to safely iterate through months
        current_month_start = start_date.replace(day=1)
        end_month_start = end_date.replace(day=1)
        
        while current_month_start <= end_month_start:
            months_to_check.add((current_month_start.year, current_month_start.month))
            # Move to next month safely
            if current_month_start.month == 12:
                current_month_start = current_month_start.replace(year=current_month_start.year + 1, month=1, day=1)
            else:
                current_month_start = current_month_start.replace(month=current_month_start.month + 1, day=1)

        # load monthly records
        monthly_map = {}
        for year, month in months_to_check:
            rec = UserMonthlyActivity.objects.filter(user_id=user_id, year=year, month=month).first()
            if rec:
                monthly_map[(year, month)] = set(rec.active_days or [])

        # count days
        count = 0
        day_cursor = start_date
        while day_cursor <= end_date:
            key = (day_cursor.year, day_cursor.month)
            if key in monthly_map and day_cursor.day in monthly_map[key]:
                count += 1
            day_cursor += timedelta(days=1)

        return count

    # ----------------------------------------------------------
    # PROFILE DESCRIPTION (uses streak_data)
    # ----------------------------------------------------------

    def generate_profile_description(
        self,
        user,
        user_tree,
        circles,
        milestones,
        monthly_activity,
        founded_groups,
        speaking_groups,
        streak_data,
    ):

        description_parts = []

        # location
        location_parts = []
        if user.village: location_parts.append(user.village.name)
        if user.subdistrict: location_parts.append(user.subdistrict.name)
        if user.district: location_parts.append(user.district.name)
        if user.state: location_parts.append(user.state.name)
        if user.country: location_parts.append(user.country.name)

        location_str = ", ".join(location_parts) if location_parts else "an unknown location"

        description_parts.append(
            f"{user.first_name} {user.last_name} is a {user.age}-year-old "
            f"{user.get_gender_display().lower()} from {location_str} "
            f"who joined on {user.date_joined.strftime('%B %d, %Y')}."
        )

        # initiator influence
        if user_tree:
            if user_tree.childcount > 0:
                description_parts.append(
                    f"As an initiator, {user.first_name} has directly brought {user_tree.childcount} members, "
                    f"with a total influence of {user_tree.influence} people."
                )

            initiation_m = [m for m in milestones if m.type == "initiation"]
            influence_m = [m for m in milestones if m.type == "influence"]

            if initiation_m:
                latest = initiation_m[0]
                description_parts.append(
                    f"They earned the title '{latest.title}' — {latest.text}."
                )

            if influence_m:
                latest = influence_m[0]
                description_parts.append(
                    f"They were recognized as '{latest.title}' — {latest.text}."
                )

        # activity streaks (your new system)
        if streak_data["days_since_join"] > 0:
            parts = []

            if streak_data["current_streak"] > 0:
                parts.append(f"currently on a {streak_data['current_streak']}-day streak")

            if streak_data["last_10_days"] > 0:
                parts.append(f"active {streak_data['last_10_days']} of the last 10 days")

            if streak_data["last_30_days"] > 0:
                parts.append(f"{streak_data['last_30_days']} days active in the last month")

            if streak_data["total_active_days"] > 0:
                parts.append(f"{streak_data['total_active_days']} total active days since joining")

            if parts:
                description_parts.append(
                    f"{user.first_name} has shown consistent support — {', '.join(parts)}."
                )
            else:
                description_parts.append(
                    f"{user.first_name} is beginning to build their activity streak."
                )

        # groups
        if founded_groups or speaking_groups:
            roles = []
            if founded_groups:
                roles.append(f"founder of {founded_groups.count()} groups")
            if speaking_groups:
                roles.append(f"speaker in {speaking_groups.count()} groups")
            description_parts.append(f"They contribute as the {', and '.join(roles)}.")

        # network relations
        relation_counts = {}
        for c in circles:
            relation_counts[c.onlinerelation] = relation_counts.get(c.onlinerelation, 0) + 1

        if relation_counts:
            rel_desc = []
            for rel, count in relation_counts.items():
                readable = dict(Circle.ONLINE_RELATION_CHOICES).get(rel, rel)
                rel_desc.append(f"{count} {readable.lower()}")
            description_parts.append(
                f"They are connected to {', '.join(rel_desc)} in their network."
            )

        return " ".join(description_parts)