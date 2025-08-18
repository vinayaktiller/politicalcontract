from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from collections import defaultdict
from geographies.models.geos import Village, Subdistrict, District, State, Country
from activity_reports.models import (
    DailyActivitySummary,
    WeeklyVillageActivityReport,
    WeeklySubdistrictActivityReport,
    WeeklyDistrictActivityReport,
    WeeklyStateActivityReport,
    WeeklyCountryActivityReport
)
from users.models import Petitioner


class Command(BaseCommand):
    help = 'Generates weekly activity reports for all geographic levels (UUID-safe)'

    def add_arguments(self, parser):
        parser.add_argument('--start-date', type=str)
        parser.add_argument('--end-date', type=str)
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **kwargs):
        start_date, end_date = self.get_date_range(kwargs)
        force = kwargs['force']

        self.stdout.write(f"Generating weekly reports from {start_date} to {end_date}")
        if force:
            self.stdout.write("Force mode: Replacing existing reports")

        self.preload_geographic_data()

        current_week_start = start_date
        processed_weeks = 0

        while current_week_start <= end_date:
            current_week_end = current_week_start + timedelta(days=6)
            week_number = current_week_start.isocalendar()[1]
            year = current_week_start.year

            self.stdout.write(f"\nProcessing week {week_number} of {year} "
                              f"({current_week_start} to {current_week_end})")

            with transaction.atomic():
                if force:
                    self.delete_existing_weekly_reports(week_number, year)

                weekly_activity = self.get_weekly_activity(current_week_start, current_week_end)
                if not weekly_activity:
                    self.stdout.write(f"No activity data for week {week_number} of {year}, skipping")
                    current_week_start += timedelta(weeks=1)
                    continue

                village_reports = self.create_village_reports(current_week_start, current_week_end, week_number, year, weekly_activity)
                subdistrict_reports = self.create_subdistrict_reports(current_week_start, current_week_end, week_number, year, village_reports, weekly_activity)
                district_reports = self.create_district_reports(current_week_start, current_week_end, week_number, year, subdistrict_reports, weekly_activity)
                state_reports = self.create_state_reports(current_week_start, current_week_end, week_number, year, district_reports, weekly_activity)
                country_reports = self.create_country_reports(current_week_start, current_week_end, week_number, year, state_reports, weekly_activity)

                self.set_parent_ids(village_reports, subdistrict_reports, district_reports, state_reports, country_reports)

            current_week_start += timedelta(weeks=1)
            processed_weeks += 1

            if processed_weeks % 5 == 0:
                self.stdout.write(f"Processed {processed_weeks} weeks...")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated weekly activity reports for {processed_weeks} weeks'
        ))

    def preload_geographic_data(self):
        self.villages = list(Village.objects.all().values('id', 'name', 'subdistrict_id'))
        self.subdistricts = list(Subdistrict.objects.all().values('id', 'name', 'district_id'))
        self.districts = list(District.objects.all().values('id', 'name', 'state_id'))
        self.states = list(State.objects.all().values('id', 'name', 'country_id'))
        self.countries = list(Country.objects.all().values('id', 'name'))

        self.user_info = {}
        for user in Petitioner.objects.only(
            'id', 'first_name', 'last_name',
            'village_id', 'subdistrict_id', 'district_id', 'state_id', 'country_id'
        ):
            self.user_info[user.id] = {
                'name': f"{user.first_name} {user.last_name}",
                'village_id': user.village_id,
                'subdistrict_id': user.subdistrict_id,
                'district_id': user.district_id,
                'state_id': user.state_id,
                'country_id': user.country_id
            }

    def delete_existing_weekly_reports(self, week_number, year):
        WeeklyVillageActivityReport.objects.filter(week_number=week_number, year=year).delete()
        WeeklySubdistrictActivityReport.objects.filter(week_number=week_number, year=year).delete()
        WeeklyDistrictActivityReport.objects.filter(week_number=week_number, year=year).delete()
        WeeklyStateActivityReport.objects.filter(week_number=week_number, year=year).delete()
        WeeklyCountryActivityReport.objects.filter(week_number=week_number, year=year).delete()

    def get_date_range(self, kwargs):
        first_activity = DailyActivitySummary.objects.order_by('date').first()
        if not first_activity:
            raise ValueError("No activity data found")

        default_start = first_activity.date - timedelta(days=first_activity.date.weekday())
        default_end = date.today() - timedelta(days=date.today().weekday() + 1)
        if default_end < default_start:
            default_end = default_start

        start_date = date.fromisoformat(kwargs['start_date']) if kwargs.get('start_date') else default_start
        end_date = date.fromisoformat(kwargs['end_date']) if kwargs.get('end_date') else default_end

        if start_date.weekday() != 0:
            start_date -= timedelta(days=start_date.weekday())

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today():
            raise ValueError("End date must be in the past")

        return start_date, end_date

    def get_weekly_activity(self, week_start, week_end):
        daily_summaries = DailyActivitySummary.objects.filter(
            date__gte=week_start,
            date__lte=week_end
        )
        if not daily_summaries:
            return None
        user_activity = defaultdict(int)
        for summary in daily_summaries:
            for uid in summary.active_users:
                user_activity[uid] += 1
        return user_activity

    # ========== UUID-safe JSON handling below ==========
    def create_village_reports(self, week_start, week_end, week_number, year, weekly_activity):
        village_users = defaultdict(lambda: defaultdict(int))
        village_reports = {}
        for uid, freq in weekly_activity.items():
            info = self.user_info.get(uid)
            if info and info['village_id']:
                village_users[info['village_id']][uid] = freq
        for vid, users in village_users.items():
            distribution = {str(i): 0 for i in range(1, 8)}
            for f in users.values():
                f = min(f, 7)
                for d in range(1, f + 1):
                    distribution[str(d)] += 1
            user_data = {
                str(uid): {
                    "id": str(uid),
                    "name": self.user_info[uid]['name'],
                    "active_days": f
                }
                for uid, f in users.items()
            }
            report = WeeklyVillageActivityReport.objects.create(
                village_id=vid,
                active_users=len(users),
                week_number=week_number,
                year=year,
                week_start_date=week_start,
                week_last_date=week_end,
                user_data=user_data,
                additional_info={"activity_distribution": distribution}
            )
            village_reports[vid] = report
        return village_reports

    def create_subdistrict_reports(self, week_start, week_end, week_number, year, village_reports, weekly_activity):
        subdistrict_activity = defaultdict(int)
        subdistrict_users = defaultdict(lambda: defaultdict(int))
        subdistrict_village_data = defaultdict(dict)
        for v in self.villages:
            sid = v['subdistrict_id']
            vid = v['id']
            if vid in village_reports:
                rep = village_reports[vid]
                subdistrict_activity[sid] += rep.active_users
                subdistrict_village_data[sid][str(vid)] = {
                    "id": str(vid),
                    "name": v['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                subdistrict_village_data[sid][str(vid)] = {
                    "id": str(vid),
                    "name": v['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in weekly_activity.items():
            info = self.user_info.get(uid)
            if info and info['subdistrict_id']:
                subdistrict_users[info['subdistrict_id']][uid] = freq
        subdistrict_reports = {}
        for sid, count in subdistrict_activity.items():
            if count > 0:
                distribution = {str(i): 0 for i in range(1, 8)}
                for f in subdistrict_users.get(sid, {}).values():
                    f = min(f, 7)
                    for d in range(1, f + 1):
                        distribution[str(d)] += 1
                rep = WeeklySubdistrictActivityReport.objects.create(
                    subdistrict_id=sid,
                    active_users=count,
                    week_number=week_number,
                    year=year,
                    week_start_date=week_start,
                    week_last_date=week_end,
                    village_data=subdistrict_village_data[sid],
                    additional_info={"activity_distribution": distribution}
                )
                subdistrict_reports[sid] = rep
        return subdistrict_reports

    def create_district_reports(self, week_start, week_end, week_number, year, subdistrict_reports, weekly_activity):
        district_activity = defaultdict(int)
        district_users = defaultdict(lambda: defaultdict(int))
        district_subdistrict_data = defaultdict(dict)
        for sd in self.subdistricts:
            did = sd['district_id']
            sid = sd['id']
            if sid in subdistrict_reports:
                rep = subdistrict_reports[sid]
                district_activity[did] += rep.active_users
                district_subdistrict_data[did][str(sid)] = {
                    "id": str(sid),
                    "name": sd['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                district_subdistrict_data[did][str(sid)] = {
                    "id": str(sid),
                    "name": sd['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in weekly_activity.items():
            info = self.user_info.get(uid)
            if info and info['district_id']:
                district_users[info['district_id']][uid] = freq
        district_reports = {}
        for did, count in district_activity.items():
            if count > 0:
                distribution = {str(i): 0 for i in range(1, 8)}
                for f in district_users.get(did, {}).values():
                    f = min(f, 7)
                    for d in range(1, f + 1):
                        distribution[str(d)] += 1
                rep = WeeklyDistrictActivityReport.objects.create(
                    district_id=did,
                    active_users=count,
                    week_number=week_number,
                    year=year,
                    week_start_date=week_start,
                    week_last_date=week_end,
                    subdistrict_data=district_subdistrict_data[did],
                    additional_info={"activity_distribution": distribution}
                )
                district_reports[did] = rep
        return district_reports

    def create_state_reports(self, week_start, week_end, week_number, year, district_reports, weekly_activity):
        state_activity = defaultdict(int)
        state_users = defaultdict(lambda: defaultdict(int))
        state_district_data = defaultdict(dict)
        for dist in self.districts:
            sid = dist['state_id']
            did = dist['id']
            if did in district_reports:
                rep = district_reports[did]
                state_activity[sid] += rep.active_users
                state_district_data[sid][str(did)] = {
                    "id": str(did),
                    "name": dist['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                state_district_data[sid][str(did)] = {
                    "id": str(did),
                    "name": dist['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in weekly_activity.items():
            info = self.user_info.get(uid)
            if info and info['state_id']:
                state_users[info['state_id']][uid] = freq
        state_reports = {}
        for sid, count in state_activity.items():
            if count > 0:
                distribution = {str(i): 0 for i in range(1, 8)}
                for f in state_users.get(sid, {}).values():
                    f = min(f, 7)
                    for d in range(1, f + 1):
                        distribution[str(d)] += 1
                rep = WeeklyStateActivityReport.objects.create(
                    state_id=sid,
                    active_users=count,
                    week_number=week_number,
                    year=year,
                    week_start_date=week_start,
                    week_last_date=week_end,
                    district_data=state_district_data[sid],
                    additional_info={"activity_distribution": distribution}
                )
                state_reports[sid] = rep
        return state_reports

    def create_country_reports(self, week_start, week_end, week_number, year, state_reports, weekly_activity):
        country_activity = defaultdict(int)
        country_users = defaultdict(lambda: defaultdict(int))
        country_state_data = defaultdict(dict)
        for state in self.states:
            cid = state['country_id']
            sid = state['id']
            if sid in state_reports:
                rep = state_reports[sid]
                country_activity[cid] += rep.active_users
                country_state_data[cid][str(sid)] = {
                    "id": str(sid),
                    "name": state['name'],
                    "active_users": rep.active_users,
                    "report_id": str(rep.id)
                }
            else:
                country_state_data[cid][str(sid)] = {
                    "id": str(sid),
                    "name": state['name'],
                    "active_users": 0,
                    "report_id": None
                }
        for uid, freq in weekly_activity.items():
            info = self.user_info.get(uid)
            if info and info['country_id']:
                country_users[info['country_id']][uid] = freq
        country_reports = {}
        for cid, count in country_activity.items():
            if count > 0:
                distribution = {str(i): 0 for i in range(1, 8)}
                for f in country_users.get(cid, {}).values():
                    f = min(f, 7)
                    for d in range(1, f + 1):
                        distribution[str(d)] += 1
                rep = WeeklyCountryActivityReport.objects.create(
                    country_id=cid,
                    active_users=count,
                    week_number=week_number,
                    year=year,
                    week_start_date=week_start,
                    week_last_date=week_end,
                    state_data=country_state_data[cid],
                    additional_info={"activity_distribution": distribution}
                )
                country_reports[cid] = rep
        return country_reports

    def set_parent_ids(self, village_reports, subdistrict_reports, district_reports, state_reports, country_reports):
        for vid, rep in village_reports.items():
            for v in self.villages:
                if v['id'] == vid:
                    sid = v['subdistrict_id']
                    if sid in subdistrict_reports:
                        rep.parent_id = subdistrict_reports[sid].id
                        rep.save()
                    break
        for sid, rep in subdistrict_reports.items():
            for sd in self.subdistricts:
                if sd['id'] == sid:
                    did = sd['district_id']
                    if did in district_reports:
                        rep.parent_id = district_reports[did].id
                        rep.save()
                    break
        for did, rep in district_reports.items():
            for dist in self.districts:
                if dist['id'] == did:
                    sid = dist['state_id']
                    if sid in state_reports:
                        rep.parent_id = state_reports[sid].id
                        rep.save()
                    break
        for sid, rep in state_reports.items():
            for s in self.states:
                if s['id'] == sid:
                    cid = s['country_id']
                    if cid in country_reports:
                        rep.parent_id = country_reports[cid].id
                        rep.save()
                    break
