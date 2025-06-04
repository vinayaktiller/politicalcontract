import logging
from django.db import models
from django.core.validators import FileExtensionValidator
from geographies.models.geos import Country, State, District, Subdistrict, Village
from prometheus_client import Counter


logger = logging.getLogger(__name__)

pendinguser_created = Counter('pendinguser_created_total', 'Total number of pending users created')

IMAGE_EXTENSIONS = [
    'bmp', 'dib', 'gif', 'jfif', 'jpe', 'jpg', 'jpeg', 'pbm', 'pgm', 'ppm', 'pnm', 'pfm', 'png', 'apng', 'blp',
    'bufr', 'cur', 'pcx', 'dcx', 'dds', 'ps', 'eps', 'fit', 'fits', 'fli', 'flc', 'ftc', 'ftu', 'gbr', 'grib',
    'h5', 'hdf', 'jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c', 'icns', 'ico', 'im', 'iim', 'mpg', 'mpeg', 'tif',
    'tiff', 'mpo', 'msp', 'palm', 'pcd', 'pdf', 'pxr', 'psd', 'qoi', 'bw', 'rgb', 'rgba', 'sgi', 'ras', 'tga',
    'icb', 'vda', 'vst', 'webp', 'wmf', 'emf', 'xbm', 'xpm'
]

GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
EVENT_CHOICES = [
    ('no_event', 'No Event'),
    ('group', 'Group Event'),
    ('public', 'Public Event'),
    ('private', 'Private Event'),
]

class PendingUser(models.Model):
    gmail = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        max_length=100,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        null=True, 
        blank=True
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)
    is_verified = models.BooleanField(default=False)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, default='no_event')
    event_id = models.BigIntegerField(null=True, blank=True)
    initiator_id = models.BigIntegerField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    class Meta:
        db_table = 'pendinguser"."pendinguser'
    
    def save(self, *args, **kwargs):
        
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            from pendingusers.services.pending_user_service import (
                handle_pending_user_creation)

            pendinguser_created.inc()
            handle_pending_user_creation(self)

    def verify_and_transfer(self):
        from pendingusers.services.pending_user_service import ( 
                verify_and_transfer_user
            )

        logger.info(f"Verifying and transferring PendingUser {self.gmail} to Petitioner")
        return verify_and_transfer_user(self)