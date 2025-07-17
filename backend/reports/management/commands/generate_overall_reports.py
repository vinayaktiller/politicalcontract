from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from geographies.models.geos import Village, Subdistrict, District, State, Country
from reports.models import OverallReport
from users.models import Petitioner
from collections import defaultdict
import json

class Command(BaseCommand):
    help = 'Generates cumulative overall reports for all geographic levels'

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
        # Preload geographic names
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
        
        # Fix parent-child relationships after all dates are processed
        self.fix_parent_ids()
        
        # Rebuild parent data fields with all child entities
        self.rebuild_parent_data_with_all_children()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully generated cumulative reports for {processed_days} days'
        ))

    def get_date_range(self, kwargs):
        # Get first user date as default start
        first_user = Petitioner.objects.order_by('date_joined').first()
        if not first_user:
            raise ValueError("No users found in database")
        default_start = first_user.date_joined.date()
        
        # Default to yesterday for end date
        default_end = date.today() - timedelta(days=1)
        
        start_date = (
            date.fromisoformat(kwargs['start_date']) 
            if kwargs.get('start_date') 
            else default_start
        )
        end_date = (
            date.fromisoformat(kwargs['end_date']) 
            if kwargs.get('end_date') 
            else default_end
        )
        
        if start_date > end_date:
            raise ValueError("Start date cannot be after end date")
        if end_date >= date.today():
            raise ValueError("End date must be in the past")
        
        return start_date, end_date

    def clean_existing_reports(self):
        OverallReport.objects.all().delete()

    def process_date(self, current_date):
        # Get new users for the date with geographic relations
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
        
        # Prepare data structures
        village_data = defaultdict(lambda: {'count': 0, 'users': {}})
        subdistrict_data = defaultdict(int)
        district_data = defaultdict(int)
        state_data = defaultdict(int)
        country_data = defaultdict(int)
        
        # Extract geographic hierarchies
        geo_hierarchy = {}
        
        # Process new users
        for user in new_users:
            village = user.village
            subdistrict = village.subdistrict
            district = subdistrict.district
            state = district.state
            country = state.country
            
            # Store IDs for parent-child relationships
            geo_hierarchy[village.id] = {
                'subdistrict_id': subdistrict.id,
                'district_id': district.id,
                'state_id': state.id,
                'country_id': country.id
            }
            
            # Aggregate counts
            village_data[village.id]['count'] += 1
            village_data[village.id]['users'][str(user.id)] = {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}"
            }
            subdistrict_data[subdistrict.id] += 1
            district_data[district.id] += 1
            state_data[state.id] += 1
            country_data[country.id] += 1
        
        # Process all levels
        with transaction.atomic():
            village_reports = self.process_villages(current_date, village_data)
            subdistrict_reports = self.process_subdistricts(
                current_date, subdistrict_data, village_reports, geo_hierarchy
            )
            district_reports = self.process_districts(
                current_date, district_data, subdistrict_reports, geo_hierarchy
            )
            state_reports = self.process_states(
                current_date, state_data, district_reports, geo_hierarchy
            )
            self.process_countries(
                current_date, country_data, state_reports, geo_hierarchy
            )

    def process_villages(self, current_date, village_data):
        reports = {}
        to_create = []
        to_update = []
        
        for village_id, data in village_data.items():
            count = data['count']
            user_data = data['users']
            
            # Get village name
            village_name = self.village_names.get(village_id, "Unknown Village")
            
            # Try to get existing report by ID
            try:
                report = OverallReport.objects.get(
                    level='village',
                    geographical_entity=village_id
                )
                # Update existing report
                report.total_users += count
                report.name = village_name
                
                # Update user data
                current_data = report.data or {}
                current_data.update(user_data)
                report.data = current_data
                
                # Update last 30 days data
                last30 = report.last30daysdata or {}
                last30[str(current_date)] = count
                report.last30daysdata = self.clean_last30days(last30, current_date)
                
                to_update.append(report)
                reports[village_id] = report
            except OverallReport.DoesNotExist:
                # Create new report with ID and name
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
        
        # Bulk operations
        if to_create:
            OverallReport.objects.bulk_create(to_create)
        if to_update:
            fields = ['name', 'total_users', 'data', 'last30daysdata']
            OverallReport.objects.bulk_update(to_update, fields)
            
        return reports

    def process_subdistricts(self, current_date, subdistrict_data, village_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 
            'subdistrict', 
            subdistrict_data, 
            village_reports, 
            geo_hierarchy,
            'village',
            'subdistrict_id',
            self.subdistrict_names
        )

    def process_districts(self, current_date, district_data, subdistrict_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 
            'district', 
            district_data, 
            subdistrict_reports, 
            geo_hierarchy,
            'subdistrict',
            'district_id',
            self.district_names
        )

    def process_states(self, current_date, state_data, district_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 
            'state', 
            state_data, 
            district_reports, 
            geo_hierarchy,
            'district',
            'state_id',
            self.state_names
        )

    def process_countries(self, current_date, country_data, state_reports, geo_hierarchy):
        return self.process_higher_level(
            current_date, 
            'country', 
            country_data, 
            state_reports, 
            geo_hierarchy,
            'state',
            'country_id',
            self.country_names
        )

    def process_higher_level(self, current_date, level, entity_data, child_reports, geo_hierarchy, child_level, parent_key, name_map):
        reports = {}
        to_create = []
        to_update = []
        
        # Find all child entities grouped by parent
        parent_children = defaultdict(list)
        for child_id, report in child_reports.items():
            parent_id = geo_hierarchy.get(child_id, {}).get(parent_key)
            if parent_id:
                parent_children[parent_id].append({
                    'id': child_id,
                    'report': report
                })
        
        for entity_id, count in entity_data.items():
            # Get geographic name
            entity_name = name_map.get(entity_id, f"Unknown {level.capitalize()}")
            
            # Get child reports for this entity
            children = parent_children.get(entity_id, [])
            
            # Try to get existing report by ID
            try:
                report = OverallReport.objects.get(
                    level=level,
                    geographical_entity=entity_id
                )
                # Update existing report
                report.total_users += count
                report.name = entity_name
                
                # Update last 30 days data
                report.last30daysdata = self.update_last30days(
                    report.last30daysdata, 
                    current_date, 
                    count
                )
                
                to_update.append(report)
                reports[entity_id] = report
            except OverallReport.DoesNotExist:
                # Create new report with ID and name
                report = OverallReport(
                    level=level,
                    geographical_entity=entity_id,
                    name=entity_name,
                    total_users=count,
                    data={},  # Will be populated in rebuild step
                    last30daysdata={str(current_date): count}
                )
                to_create.append(report)
                reports[entity_id] = report
            
            # Set parent IDs for children
            for child in children:
                child_report = child['report']
                if child_report.parent_id != report.id:
                    child_report.parent_id = report.id
                    child_report.save(update_fields=['parent_id'])
        
        # Bulk operations
        if to_create:
            OverallReport.objects.bulk_create(to_create)
        if to_update:
            fields = ['name', 'total_users', 'last30daysdata']
            OverallReport.objects.bulk_update(to_update, fields)
            
        return reports

    def clean_last30days(self, last30days, current_date):
        """Maintain only the last 30 days of data"""
        if not last30days:
            return {}
        
        cutoff = current_date - timedelta(days=30)
        return {
            d: c for d, c in last30days.items() 
            if date.fromisoformat(d) > cutoff
        }

    def update_last30days(self, last30days, current_date, count):
        """Update last 30 days data with new count"""
        current_data = last30days or {}
        current_data[str(current_date)] = count
        return self.clean_last30days(current_data, current_date)
    
    def fix_parent_ids(self):
        """Ensure all reports have correct parent IDs"""
        self.stdout.write("Fixing parent-child relationships...")
        
        # Fix village -> subdistrict relationships
        villages = OverallReport.objects.filter(level='village', parent_id__isnull=True)
        for village_report in villages:
            try:
                village = Village.objects.get(id=village_report.geographical_entity)
                subdistrict_report = OverallReport.objects.get(
                    level='subdistrict',
                    geographical_entity=village.subdistrict_id
                )
                village_report.parent_id = subdistrict_report.id
                village_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing village {village_report.id}: {str(e)}")
        
        # Fix subdistrict -> district relationships
        subdistricts = OverallReport.objects.filter(level='subdistrict', parent_id__isnull=True)
        for subdistrict_report in subdistricts:
            try:
                subdistrict = Subdistrict.objects.get(id=subdistrict_report.geographical_entity)
                district_report = OverallReport.objects.get(
                    level='district',
                    geographical_entity=subdistrict.district_id
                )
                subdistrict_report.parent_id = district_report.id
                subdistrict_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing subdistrict {subdistrict_report.id}: {str(e)}")
        
        # Fix district -> state relationships
        districts = OverallReport.objects.filter(level='district', parent_id__isnull=True)
        for district_report in districts:
            try:
                district = District.objects.get(id=district_report.geographical_entity)
                state_report = OverallReport.objects.get(
                    level='state',
                    geographical_entity=district.state_id
                )
                district_report.parent_id = state_report.id
                district_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing district {district_report.id}: {str(e)}")
        
        # Fix state -> country relationships
        states = OverallReport.objects.filter(level='state', parent_id__isnull=True)
        for state_report in states:
            try:
                state = State.objects.get(id=state_report.geographical_entity)
                country_report = OverallReport.objects.get(
                    level='country',
                    geographical_entity=state.country_id
                )
                state_report.parent_id = country_report.id
                state_report.save(update_fields=['parent_id'])
            except Exception as e:
                self.stdout.write(f"Error fixing state {state_report.id}: {str(e)}")
        
        self.stdout.write("Parent-child relationships fixed")
    
    def rebuild_parent_data_with_all_children(self):
        """Rebuild data fields for parent levels to include ALL child entities"""
        self.stdout.write("Rebuilding parent data fields with ALL children...")
        
        # Define parent-child relationships with models and foreign keys
        level_map = [
            ('subdistrict', 'village', Village, 'subdistrict_id'),
            ('district', 'subdistrict', Subdistrict, 'district_id'),
            ('state', 'district', District, 'state_id'),
            ('country', 'state', State, 'country_id')
        ]
        
        for parent_level, child_level, child_model, parent_fk in level_map:
            self.stdout.write(f"Processing {parent_level} level...")
            
            # Preload all child geographical entities grouped by parent ID
            children_by_parent = defaultdict(list)
            for child in child_model.objects.all().values('id', 'name', parent_fk):
                parent_id = child[parent_fk]
                children_by_parent[parent_id].append({
                    'id': child['id'],
                    'name': child['name']
                })
            
            # Preload existing child reports
            child_reports = {
                r.geographical_entity: r 
                for r in OverallReport.objects.filter(level=child_level)
            }
            
            # Process each parent report
            parent_reports = OverallReport.objects.filter(level=parent_level)
            to_update = []
            
            for parent_report in parent_reports:
                parent_geo_id = parent_report.geographical_entity
                children_data = {}
                
                # Get all geographical children for this parent
                geo_children = children_by_parent.get(parent_geo_id, [])
                
                for child in geo_children:
                    child_id = child['id']
                    child_report = child_reports.get(child_id)
                    
                    # Create entry with zero values if no report exists
                    if child_report:
                        children_data[str(child_id)] = {
                            'id': child_id,
                            'name': child['name'],
                            'total_users': child_report.total_users,
                            'report_id': child_report.id
                        }
                    else:
                        children_data[str(child_id)] = {
                            'id': child_id,
                            'name': child['name'],
                            'total_users': 0,
                            'report_id': None
                        }
                
                # Only update if changed
                if parent_report.data != children_data:
                    parent_report.data = children_data
                    to_update.append(parent_report)
            
            # Bulk update
            if to_update:
                OverallReport.objects.bulk_update(to_update, ['data'])
                self.stdout.write(f"Updated {len(to_update)} {parent_level} reports")
        
        self.stdout.write("Parent data fields rebuilt with ALL children")