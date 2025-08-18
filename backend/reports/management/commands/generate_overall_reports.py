from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import OverallReport
from users.models import Petitioner
from collections import defaultdict


class Command(BaseCommand):
    help = 'Generates cumulative overall reports for all geographic levels (UUID-safe)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: first user date)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: yesterday)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete existing reports before processing'
        )

    def handle(self, *args, **kwargs):
        # Preload geographic names - keep UUID keys
        self.village_names = {v.id: v.name for v in Village.objects.all()}
        self.subdistrict_names = {s.id: s.name for s in Subdistrict.objects.all()}
        self.district_names = {d.id: d.name for d in District.objects.all()}
        self.state_names = {s.id: s.name for s in State.objects.all()}
        self.country_names = {c.id: c.name for c in Country.objects.all()}

        start_date, end_date = self.get_date_range(kwargs)

        if kwargs['clean']:
            self.clean_existing_reports()
            self.stdout.write("Cleaned existing reports")

        self.stdout.write(f"Generating cumulative reports from {start_date} to {end_date}")
        current_date = start_date
        processed_days = 0

        while current_date <= end_date:
            self.stdout.write(f"Processing {current_date}...")
            self.process_date(current_date)
            current_date += timedelta(days=1)
            processed_days += 1

            if processed_days % 10 == 0:
                self.stdout.write(f"Processed {processed_days} days...")

        self.fix_parent_ids()
        self.rebuild_parent_data_with_all_children()

        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated cumulative reports for {processed_days} days'
        ))

    def get_date_range(self, kwargs):
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            raise ValueError("No users found in database")
        default_start = first_user.date_joined.date()
        default_end = date.today() - timedelta(days=1)

        start_date = (
            date.fromisoformat(kwargs['start_date'])
            if kwargs.get('start_date') else default_start
        )
        end_date = (
            date.fromisoformat(kwargs['end_date'])
            if kwargs.get('end_date') else default_end
        )

        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today():
            raise ValueError("End date must be in the past")

        return start_date, end_date

    def clean_existing_reports(self):
        OverallReport.objects.all().delete()

    def process_date(self, current_date):
        new_users = Petitioner.objects.filter(
            date_joined__date=current_date
        ).exclude(
            village__isnull=True,
            subdistrict__isnull=True,
            district__isnull=True,
            state__isnull=True,
            country__isnull=True
        ).select_related(
            'village', 'village__subdistrict',
            'village__subdistrict__district',
            'village__subdistrict__district__state',
            'village__subdistrict__district__state__country'
        )

        village_data = defaultdict(lambda: {'count': 0, 'users': {}})
        subdistrict_data = defaultdict(int)
        district_data = defaultdict(int)
        state_data = defaultdict(int)
        country_data = defaultdict(int)

        geo_hierarchy = {}

        for user in new_users:
            village = user.village
            subdistrict = village.subdistrict
            district = subdistrict.district
            state = district.state
            country = state.country

            geo_hierarchy[village.id] = {
                'subdistrict_id': subdistrict.id,
                'district_id': district.id,
                'state_id': state.id,
                'country_id': country.id
            }

            village_data[village.id]['count'] += 1
            village_data[village.id]['users'][str(user.id)] = {
                'id': str(user.id),
                'name': f"{user.first_name} {user.last_name}"
            }
            subdistrict_data[subdistrict.id] += 1
            district_data[district.id] += 1
            state_data[state.id] += 1
            country_data[country.id] += 1

        with transaction.atomic():
            village_reports = self.process_villages(current_date, village_data)
            subdistrict_reports = self.process_subdistricts(current_date, subdistrict_data, village_reports, geo_hierarchy)
            district_reports = self.process_districts(current_date, district_data, subdistrict_reports, geo_hierarchy)
            state_reports = self.process_states(current_date, state_data, district_reports, geo_hierarchy)
            self.process_countries(current_date, country_data, state_reports, geo_hierarchy)

    def process_villages(self, current_date, village_data):
        reports, to_create, to_update = {}, [], []
        for village_id, data in village_data.items():
            count = data['count']
            user_data = data['users']
            village_name = self.village_names.get(village_id, "Unknown Village")
            try:
                report = OverallReport.objects.get(
                    level='village', geographical_entity=village_id
                )
                report.total_users += count
                report.name = village_name
                current_data = report.data or {}
                current_data.update(user_data)
                report.data = current_data
                last30 = report.last30daysdata or {}
                last30[str(current_date)] = count
                report.last30daysdata = self.clean_last30days(last30, current_date)
                to_update.append(report)
            except OverallReport.DoesNotExist:
                report = OverallReport(
                    level='village',
                    geographical_entity=village_id,
                    name=village_name,
                    total_users=count,
                    data=user_data,
                    last30daysdata={str(current_date): count}
                )
                to_create.append(report)
            reports[village_id] = report
        if to_create:
            OverallReport.objects.bulk_create(to_create)
        if to_update:
            OverallReport.objects.bulk_update(to_update, ['name', 'total_users', 'data', 'last30daysdata'])
        return reports

    def process_subdistricts(self, current_date, subdistrict_data, village_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 'subdistrict', subdistrict_data, village_reports,
            geo_hierarchy, 'village', 'subdistrict_id', self.subdistrict_names
        )

    def process_districts(self, current_date, district_data, subdistrict_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 'district', district_data, subdistrict_reports,
            geo_hierarchy, 'subdistrict', 'district_id', self.district_names
        )

    def process_states(self, current_date, state_data, district_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 'state', state_data, district_reports,
            geo_hierarchy, 'district', 'state_id', self.state_names
        )

    def process_countries(self, current_date, country_data, state_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 'country', country_data, state_reports,
            geo_hierarchy, 'state', 'country_id', self.country_names
        )

    def process_higher_level(self, current_date, level, entity_data, child_reports, geo_hierarchy, child_level, parent_key, name_map):
        reports, to_create, to_update = {}, [], []
        parent_children = defaultdict(list)
        for child_id, report in child_reports.items():
            parent_id = geo_hierarchy.get(child_id, {}).get(parent_key)
            if parent_id:
                parent_children[parent_id].append({
                    'id': child_id,
                    'report': report
                })
        for entity_id, count in entity_data.items():
            entity_name = name_map.get(entity_id, f"Unknown {level.capitalize()}")
            children = parent_children.get(entity_id, [])
            try:
                report = OverallReport.objects.get(
                    level=level, geographical_entity=entity_id
                )
                report.total_users += count
                report.name = entity_name
                report.last30daysdata = self.update_last30days(report.last30daysdata, current_date, count)
                to_update.append(report)
            except OverallReport.DoesNotExist:
                report = OverallReport(
                    level=level,
                    geographical_entity=entity_id,
                    name=entity_name,
                    total_users=count,
                    data={},
                    last30daysdata={str(current_date): count}
                )
                to_create.append(report)
            reports[entity_id] = report
            for child in children:
                if child['report'].parent_id != report.id:
                    child['report'].parent_id = report.id
                    child['report'].save(update_fields=['parent_id'])
        if to_create:
            OverallReport.objects.bulk_create(to_create)
        if to_update:
            OverallReport.objects.bulk_update(to_update, ['name', 'total_users', 'last30daysdata'])
        return reports

    def clean_last30days(self, last30days, current_date):
        if not last30days:
            return {}
        cutoff = current_date - timedelta(days=30)
        return {d: c for d, c in last30days.items() if date.fromisoformat(d) > cutoff}

    def update_last30days(self, last30days, current_date, count):
        current_data = last30days or {}
        current_data[str(current_date)] = count
        return self.clean_last30days(current_data, current_date)

    def fix_parent_ids(self):
        self.stdout.write("Fixing parent-child relationships...")
        for village_report in OverallReport.objects.filter(level='village', parent_id__isnull=True):
            try:
                village = Village.objects.get(id=village_report.geographical_entity)
                subdistrict_report = OverallReport.objects.get(
                    level='subdistrict', geographical_entity=village.subdistrict_id
                )
                village_report.parent_id = subdistrict_report.id
                village_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing village {village_report.id}: {e}")
        for sub_report in OverallReport.objects.filter(level='subdistrict', parent_id__isnull=True):
            try:
                subdistrict = Subdistrict.objects.get(id=sub_report.geographical_entity)
                district_report = OverallReport.objects.get(
                    level='district', geographical_entity=subdistrict.district_id
                )
                sub_report.parent_id = district_report.id
                sub_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing subdistrict {sub_report.id}: {e}")
        for dist_report in OverallReport.objects.filter(level='district', parent_id__isnull=True):
            try:
                district = District.objects.get(id=dist_report.geographical_entity)
                state_report = OverallReport.objects.get(
                    level='state', geographical_entity=district.state_id
                )
                dist_report.parent_id = state_report.id
                dist_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing district {dist_report.id}: {e}")
        for state_report in OverallReport.objects.filter(level='state', parent_id__isnull=True):
            try:
                state = State.objects.get(id=state_report.geographical_entity)
                country_report = OverallReport.objects.get(
                    level='country', geographical_entity=state.country_id
                )
                state_report.parent_id = country_report.id
                state_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing state {state_report.id}: {e}")
        self.stdout.write("Parent-child relationships fixed")

    def rebuild_parent_data_with_all_children(self):
        self.stdout.write("Rebuilding parent data fields with ALL children...")
        level_map = [
            ('subdistrict', 'village', Village, 'subdistrict_id'),
            ('district', 'subdistrict', Subdistrict, 'district_id'),
            ('state', 'district', District, 'state_id'),
            ('country', 'state', State, 'country_id')
        ]
        for parent_level, child_level, child_model, parent_fk in level_map:
            self.stdout.write(f"Processing {parent_level} level...")
            children_by_parent = defaultdict(list)
            # Keep UUID as UUID object for lookups
            for child in child_model.objects.all().values('id', 'name', parent_fk):
                children_by_parent[child[parent_fk]].append({
                    'id': child['id'],  # UUID object
                    'name': child['name']
                })
            child_reports = {
                r.geographical_entity: r
                for r in OverallReport.objects.filter(level=child_level)
            }
            parent_reports = OverallReport.objects.filter(level=parent_level)
            to_update = []
            for parent_report in parent_reports:
                parent_geo_id = parent_report.geographical_entity
                children_data = {}
                for child in children_by_parent.get(parent_geo_id, []):
                    cr = child_reports.get(child['id'])
                    children_data[str(child['id'])] = {
                        'id': str(child['id']),
                        'name': child['name'],
                        'total_users': cr.total_users if cr else 0,
                        'report_id': str(cr.id) if cr else None
                    }
                if parent_report.data != children_data:
                    parent_report.data = children_data
                    to_update.append(parent_report)
            if to_update:
                OverallReport.objects.bulk_update(to_update, ['data'])
                self.stdout.write(f"Updated {len(to_update)} {parent_level} reports")
        self.stdout.write("Parent data fields rebuilt with ALL children")
