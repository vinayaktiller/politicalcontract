from django.db import models
from django.utils import timezone
import logging


logger = logging.getLogger(__name__)

# Activity milestones definition
ACTIVITY_MILESTONES = {
    5: (
        "Nurse",
        "You have shown support for 5 days — you are nursing the birth of this movement and keeping its first breaths steady."
    ),
    10: (
        "Parent",
        "You have shown support for 10 days — like a parent caring for a child, you consistently nurture this cause and help it grow day by day."
    ),
    25: (
        "Barber",
        "You have shown support for 25 days — like a barber who grooms and refreshes faces, you refine the movement's public presence and help it appear confident and well-kept."
    ),
    50: (
        "Leather scroll",
        "You have shown support for 50 days — like a leather scroll that preserves important records, your steady contributions are being preserved in the movement's history and will inspire many."
    ),
    75: (
        "Provisioner",
        "You have shown support for 75 days — like a toddy-tapper who gathers sustenance or a cook who transforms it into food, you are fueling the movement: providing energy, nourishment, and the everyday labour that keeps it alive."
    ),
    100: (
        "Sculptor",
        "You have shown support for 100 days — through steady work you have begun to shape the movement itself. What was once raw is taking form; your effort leaves a lasting, crafted impression."
    ),
    150: (
        "Herder",
        "You have shown support for 150 days — like a herder who tends cattle across seasons, you guard the movement's wellbeing: feeding it, protecting it, and guiding it with steady commitment."
    ),
    200: (
        "Driver",
        "You have shown support for 200 days — whether as a bus driver carrying people forward or a loco-pilot powering a train ahead, you keep the movement in motion with direction, stability, and unstoppable momentum."
    ),
    250: (
        "Activist",
        "You have shown support for 250 days — you stand as an activist of this movement: showing up every day, sustaining its pulse, and keeping the demand alive through your consistent action."
    ),
    300: (
        "Advocate",
        "You have shown support for 300 days — your long and unwavering dedication makes you a true advocate of this movement, someone who stands for the cause with remarkable consistency and conviction."
    ),
}

class AdditionalInfo(models.Model):
    user_id = models.BigIntegerField(primary_key=True)
    
    # Geographical sequence numbers
    village_number = models.PositiveIntegerField()
    subdistrict_number = models.PositiveIntegerField()
    district_number = models.PositiveIntegerField()
    state_number = models.PositiveIntegerField()
    country_number = models.PositiveIntegerField()
    
    # Activity tracking
    active_days = models.PositiveIntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'userschema"."additional_info'
        verbose_name = 'Additional User Information'
        verbose_name_plural = 'Additional User Information'
    
    def __str__(self):
        return f"Additional info for user {self.user_id}"
    
    def update_active_days(self, activity_date=None):
        """Update active days count and check for milestones"""
        from users.models import Petitioner
        
        today = activity_date or timezone.now().date()
        
        # Only update if not already active today
        if self.last_active_date != today:
            old_active_days = self.active_days
            self.active_days += 1
            self.last_active_date = today
            self.save(update_fields=['active_days', 'last_active_date'])
            
            logger.info(f"Updated active days for user {self.user_id}: {old_active_days} -> {self.active_days}")
            
            # Check for milestones
            self.check_activity_milestones()
            return True
        return False
    
    def check_activity_milestones(self):
        """Check and create activity milestones based on total active days"""
        try:
            from users.models import Milestone, Petitioner
            
            
            # Check if current active_days reaches any milestone
            if self.active_days in ACTIVITY_MILESTONES:
                title, text = ACTIVITY_MILESTONES[self.active_days]
                
                # Check if milestone already exists for this user and level
                if not Milestone.objects.filter(
                    user_id=self.user_id, 
                    title=title,
                    type='heartbeat'
                ).exists():
                    
                    # Get user gender for photo_id calculation
                    try:
                        user = Petitioner.objects.get(id=self.user_id)
                        gender = user.gender
                    except Petitioner.DoesNotExist:
                        gender = 'M'  # Default to Male if user not found
                    
                    # Calculate photo_id based on milestone level and gender
                    photo_id = self.calculate_activity_photo_id(self.active_days, gender)
                    
                    # Create the milestone
                    Milestone.objects.create(
                        user_id=self.user_id,
                        title=title,
                        text=text,
                        type='heartbeat',
                        photo_id=photo_id,
                        created_at=timezone.now()
                    )
                    
                    logger.info(f"Created activity milestone '{title}' for user {self.user_id} with {self.active_days} active days")
        
        except ImportError:
            logger.error("Milestone model not found - cannot create activity milestones")
        except Exception as e:
            logger.error(f"Error creating activity milestone for user {self.user_id}: {str(e)}")
    
    def calculate_activity_photo_id(self, total_active_days, gender):
        """Calculate photo_id for activity milestones based on level and gender"""
        try:
            # Get sorted milestone levels
            levels = sorted(ACTIVITY_MILESTONES.keys())
            milestone_index = levels.index(total_active_days)
            
            # Gender offset: 0 for Male, 1 for Female
            gender_offset = 0 if gender in ['M', 'Male'] else 1
            
            # Calculate photo_id (starting from 1 for first milestone)
            photo_id = milestone_index * 2 + gender_offset + 1
            
            return photo_id
            
        except (ValueError, IndexError):
            logger.error(f"Could not calculate photo_id for activity level {total_active_days}")
            return None