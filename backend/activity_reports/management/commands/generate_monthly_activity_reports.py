from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from collections import defaultdict
import calendar
from geographies.models.geos import Village, Subdistrict, District, State, Country
from activity_reports.models import (
    DailyActivitySummary,
    MonthlyVillageActivityReport,
    MonthlySubdistrictActivityReport,
    MonthlyDistrictActivityReport,
    MonthlyStateActivityReport,
    MonthlyCountryActivityReport
)
from users.models import Petitioner


class Command(BaseCommand):
    help = 'Generates monthly activity reports for all geographic levels'

    ACTIVITY_BUCKETS = [1, 5, 10, 15, 20, 25, 30]

    def add_arguments(self, parser):
        parser.add_argument('--start-date', type=str)
        parser.add_argument('--end-date', type=str)
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        force = kwargs['force']

        self.stdout.write(f"Generating monthly reports from {start_date} to {end_date}")
        if force:
            self.stdout.write("Force mode: Replacing existing reports")

        self.preload_geographic_data()

        current_date = start_date
        processed_months = 0

        while current_date <= end_date:
            first_day = date(current_date.year, current_date.month, 1)
            last_day = date(
                current_date.year,
                current_date.month,
                calendar.monthrange(current_date.year, current_date.month)[1]
            )

            self.stdout.write(f"\nProcessing {first_day.strftime('%B %Y')} ({first_day} to {last_day})")

            with transaction.atomic():
                if force:
                    self.delete_existing_monthly_reports(current_date.month, current_date.year)

                monthly_activity = self.get_monthly_activity(first_day, last_day)
                if not monthly_activity:
                    self.stdout.write(f"No activity data for {first_day.strftime('%B %Y')}, skipping")
                    current_date = self.next_month(current_date)
                    continue

                village_reports = self.create_village_reports(first_day, last_day, current_date.month, current_date.year, monthly_activity)
                subdistrict_reports = self.create_subdistrict_reports(first_day, last_day, current_date.month, current_date.year, village_reports, monthly_activity)
                district_reports = self.create_district_reports(first_day, last_day, current_date.month, current_date.year, subdistrict_reports, monthly_activity)
                state_reports = self.create_state_reports(first_day, last_day, current_date.month, current_date.year, district_reports, monthly_activity)
                country_reports = self.create_country_reports(first_day, last_day, current_date.month, current_date.year, state_reports, monthly_activity)

                self.set_parent_ids(village_reports, subdistrict_reports, district_reports, state_reports, country_reports)

            current_date = self.next_month(current_date)
            processed_months += 1

            if processed_months % 3 == 0:
                self.stdout.write(f"Processed {processed_months} months...")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated monthly activity reports for {processed_months} months'
        ))

    def preload_geographic_data(self):
        self.villages = list(Village.objects.all().values('id', 'name', 'subdistrict_id'))
        self.subdistricts = list(Subdistrict.objects.all().values('id', 'name', 'district_id'))
        self.districts = list(District.objects.all().values('id', 'name', 'state_id'))
        self.states = list(State.objects.all().values('id', 'name', 'country_id'))
        self.countries = list(Country.objects.all().values('id', 'name'))

        self.user_info = {}
        for user in Petitioner.objects.only('id', 'first_name', 'last_name', 'village_id', 'subdistrict_id', 'district_id', 'state_id', 'country_id'):
            self.user_info[user.id] = {
                'name': f"{user.first_name} {user.last_name}",
                'village_id': user.village_id,
                'subdistrict_id': user.subdistrict_id,
                'district_id': user.district_id,
                'state_id': user.state_id,
                'country_id': user.country_id
            }

    def next_month(self, dt):
        return date(dt.year + 1, 1, 1) if dt.month == 12 else date(dt.year, dt.month + 1, 1)

    def delete_existing_monthly_reports(self, month, year):
        MonthlyVillageActivityReport.objects.filter(month=month, year=year).delete()
        MonthlySubdistrictActivityReport.objects.filter(month=month, year=year).delete()
        MonthlyDistrictActivityReport.objects.filter(month=month, year=year).delete()
        MonthlyStateActivityReport.objects.filter(month=month, year=year).delete()
        MonthlyCountryActivityReport.objects.filter(month=month, year=year).delete()

    def get_date_range(self, kwargs):
        first_activity = DailyActivitySummary.objects.order_by('date').first()
        if not first_activity:
            raise ValueError("No activity data found in database")
        default_start = first_activity.date.replace(day=1)
        today = date.today()
        default_end = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
        if default_end < default_start:
            default_end = default_start
        start_date = date.fromisoformat(kwargs['start_date']) if kwargs.get('start_date') else default_start
        end_date = date.fromisoformat(kwargs['end_date']) if kwargs.get('end_date') else default_end
        start_date = start_date.replace(day=1)
        end_date = end_date.replace(day=1)
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today().replace(day=1):
            raise ValueError("End date must be in the past")
        return start_date, end_date

    def get_monthly_activity(self, month_start, month_end):
        daily_summaries = DailyActivitySummary.objects.filter(
            date__gte=month_start,
            date__lte=month_end
        )
        if not daily_summaries:
            return None
        user_activity = defaultdict(int)
        for summary in daily_summaries:
            for user_id in summary.active_users:
                user_activity[user_id] += 1
        return user_activity

    def calculate_activity_distribution(self, frequencies):
        distribution = {str(bucket): 0 for bucket in self.ACTIVITY_BUCKETS}
        for freq in frequencies:
            for bucket in self.ACTIVITY_BUCKETS:
                if freq >= bucket:
                    distribution[str(bucket)] += 1
        return distribution

    # ===== UUID-safe JSON in all create_x_reports methods =====
    def create_village_reports(self, month_start, month_end, month, year, monthly_activity):
        village_users = defaultdict(lambda: defaultdict(int))
        village_reports = {}
        for user_id, freq in monthly_activity.items():
            info = self.user_info.get(user_id)
            if info and info['village_id']:
                village_users[info['village_id']][user_id] = freq
        for village_id, users in village_users.items():
            distribution = self.calculate_activity_distribution(users.values())
            user_data = {
                str(uid): {
                    "id": str(uid),
                    "name": self.user_info[uid]['name'],
                    "active_days": freq
                }
                for uid, freq in users.items()
            }
            report = MonthlyVillageActivityReport.objects.create(
                village_id=village_id,
                active_users=len(users),
                month=month,
                year=year,
                last_date=month_end,
                user_data=user_data,
                additional_info={"activity_distribution": distribution}
            )
            village_reports[village_id] = report
        return village_reports

    def create_subdistrict_reports(self, month_start, month_end, month, year, village_reports, monthly_activity):
        subdistrict_activity = defaultdict(int)
        subdistrict_users = defaultdict(lambda: defaultdict(int))
        subdistrict_village_reports = defaultdict(dict)
        for village in self.villages:
            sid = village['subdistrict_id']
            vid = village['id']
            if vid in village_reports:
                rep = village_reports[vid]
                subdistrict_activity[sid] += rep.active_users
                subdistrict_village_reports[sid][str(vid)] = {
                    "id": str(vid),
                    "name": village['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                subdistrict_village_reports[sid][str(vid)] = {
                    "id": str(vid),
                    "name": village['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in monthly_activity.items():
            info = self.user_info.get(uid)
            if info and info['subdistrict_id']:
                subdistrict_users[info['subdistrict_id']][uid] = freq
        subdistrict_reports = {}
        for sid, active_count in subdistrict_activity.items():
            if active_count > 0:
                dist = self.calculate_activity_distribution(subdistrict_users.get(sid, {}).values())
                report = MonthlySubdistrictActivityReport.objects.create(
                    subdistrict_id=sid,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    village_data=subdistrict_village_reports[sid],
                    additional_info={"activity_distribution": dist}
                )
                subdistrict_reports[sid] = report
        return subdistrict_reports

    def create_district_reports(self, month_start, month_end, month, year, subdistrict_reports, monthly_activity):
        district_activity = defaultdict(int)
        district_users = defaultdict(lambda: defaultdict(int))
        district_subdistrict_reports = defaultdict(dict)
        for sub in self.subdistricts:
            did = sub['district_id']
            sid = sub['id']
            if sid in subdistrict_reports:
                rep = subdistrict_reports[sid]
                district_activity[did] += rep.active_users
                district_subdistrict_reports[did][str(sid)] = {
                    "id": str(sid),
                    "name": sub['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                district_subdistrict_reports[did][str(sid)] = {
                    "id": str(sid),
                    "name": sub['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in monthly_activity.items():
            info = self.user_info.get(uid)
            if info and info['district_id']:
                district_users[info['district_id']][uid] = freq
        district_reports = {}
        for did, active_count in district_activity.items():
            if active_count > 0:
                dist = self.calculate_activity_distribution(district_users.get(did, {}).values())
                report = MonthlyDistrictActivityReport.objects.create(
                    district_id=did,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    subdistrict_data=district_subdistrict_reports[did],
                    additional_info={"activity_distribution": dist}
                )
                district_reports[did] = report
        return district_reports

    def create_state_reports(self, month_start, month_end, month, year, district_reports, monthly_activity):
        state_activity = defaultdict(int)
        state_users = defaultdict(lambda: defaultdict(int))
        state_district_reports = defaultdict(dict)
        for dist in self.districts:
            sid = dist['state_id']
            did = dist['id']
            if did in district_reports:
                rep = district_reports[did]
                state_activity[sid] += rep.active_users
                state_district_reports[sid][str(did)] = {
                    "id": str(did),
                    "name": dist['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                state_district_reports[sid][str(did)] = {
                    "id": str(did),
                    "name": dist['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in monthly_activity.items():
            info = self.user_info.get(uid)
            if info and info['state_id']:
                state_users[info['state_id']][uid] = freq
        state_reports = {}
        for sid, active_count in state_activity.items():
            if active_count > 0:
                dist = self.calculate_activity_distribution(state_users.get(sid, {}).values())
                report = MonthlyStateActivityReport.objects.create(
                    state_id=sid,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    district_data=state_district_reports[sid],
                    additional_info={"activity_distribution": dist}
                )
                state_reports[sid] = report
        return state_reports

    def create_country_reports(self, month_start, month_end, month, year, state_reports, monthly_activity):
        country_activity = defaultdict(int)
        country_users = defaultdict(lambda: defaultdict(int))
        country_state_reports = defaultdict(dict)
        for state in self.states:
            cid = state['country_id']
            sid = state['id']
            if sid in state_reports:
                rep = state_reports[sid]
                country_activity[cid] += rep.active_users
                country_state_reports[cid][str(sid)] = {
                    "id": str(sid),
                    "name": state['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                country_state_reports[cid][str(sid)] = {
                    "id": str(sid),
                    "name": state['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in monthly_activity.items():
            info = self.user_info.get(uid)
            if info and info['country_id']:
                country_users[info['country_id']][uid] = freq
        country_reports = {}
        for cid, active_count in country_activity.items():
            if active_count > 0:
                dist = self.calculate_activity_distribution(country_users.get(cid, {}).values())
                report = MonthlyCountryActivityReport.objects.create(
                    country_id=cid,
                    active_users=active_count,
                    month=month,
                    year=year,
                    last_date=month_end,
                    state_data=country_state_reports[cid],
                    additional_info={"activity_distribution": dist}
                )
                country_reports[cid] = report
        return country_reports

    def set_parent_ids(self, village_reports, subdistrict_reports, district_reports, state_reports, country_reports):
        for vid, report in village_reports.items():
            for v in self.villages:
                if v['id'] == vid:
                    sid = v['subdistrict_id']
                    if sid in subdistrict_reports:
                        report.parent_id = subdistrict_reports[sid].id
                        report.save()
                    break
        for sid, report in subdistrict_reports.items():
            for sd in self.subdistricts:
                if sd['id'] == sid:
                    did = sd['district_id']
                    if did in district_reports:
                        report.parent_id = district_reports[did].id
                        report.save()
                    break
        for did, report in district_reports.items():
            for dist in self.districts:
                if dist['id'] == did:
                    sid = dist['state_id']
                    if sid in state_reports:
                        report.parent_id = state_reports[sid].id
                        report.save()
                    break
        for sid, report in state_reports.items():
            for s in self.states:
                if s['id'] == sid:
                    cid = s['country_id']
                    if cid in country_reports:
                        report.parent_id = country_reports[cid].id
                        report.save()
                    break
