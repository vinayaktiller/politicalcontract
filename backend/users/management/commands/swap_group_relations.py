from django.core.management.base import BaseCommand
from users.models import Circle  # Replace 'your_app' with your actual app name

class Command(BaseCommand):
    help = 'Swaps groupagent and groupmembers values in Circle.onlinerelation field'

    def handle(self, *args, **options):
        # Temporary value for safe swap
        TEMP_VALUE = 'temp_swap_value'

        # Update groupagent -> TEMP_VALUE
        Circle.objects.filter(onlinerelation='groupagent').update(onlinerelation=TEMP_VALUE)
        self.stdout.write(self.style.SUCCESS('Moved groupagent to temporary storage'))

        # Update groupmembers -> groupagent
        Circle.objects.filter(onlinerelation='groupmembers').update(onlinerelation='groupagent')
        self.stdout.write(self.style.SUCCESS('Converted groupmembers to groupagent'))

        # Update TEMP_VALUE (original groupagent) -> groupmembers
        Circle.objects.filter(onlinerelation=TEMP_VALUE).update(onlinerelation='groupmembers')
        self.stdout.write(self.style.SUCCESS('Converted temporary values to groupmembers'))

        # Final success message
        updated_groupagent = Circle.objects.filter(onlinerelation='groupagent').count()
        updated_groupmembers = Circle.objects.filter(onlinerelation='groupmembers').count()
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully swapped values! '
            f'New counts: groupagent={updated_groupagent}, groupmembers={updated_groupmembers}'
        ))