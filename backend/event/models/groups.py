from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.core.validators import FileExtensionValidator
from geographies.models.geos import Country, State, District, Subdistrict, Village
from backend.azure_storage import AzureMediaStorage

# Image extensions for validation
IMAGE_EXTENSIONS = [
    'bmp', 'dib', 'gif', 'jfif', 'jpe', 'jpg', 'jpeg', 'pbm', 'pgm', 'ppm', 'pnm', 'pfm', 'png', 'apng', 'blp',
    'bufr', 'cur', 'pcx', 'dcx', 'dds', 'ps', 'eps', 'fit', 'fits', 'fli', 'flc', 'ftc', 'ftu', 'gbr', 'grib',
    'h5', 'hdf', 'jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c', 'icns', 'ico', 'im', 'iim', 'mpg', 'mpeg', 'tif',
    'tiff', 'mpo', 'msp', 'palm', 'pcd', 'pdf', 'pxr', 'psd', 'qoi', 'bw', 'rgb', 'rgba', 'sgi', 'ras', 'tga',
    'icb', 'vda', 'vst', 'webp', 'wmf', 'emf', 'xbm', 'xpm'
]

class Group(models.Model):
    name = models.CharField(max_length=255)
    founder = models.BigIntegerField()
    
    # profile_pic = models.URLField(
    #     max_length=500,
    #     blank=True,
    #     null=True,
    #     help_text="URL for the group's main profile picture"
    # )
    
    profile_pic = models.ImageField(
        upload_to='group_profile_pics/',
        storage=AzureMediaStorage(),
        max_length=500,
        validators=[FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)],
        null=True,
        blank=True,
        help_text="Profile picture for the group"
    )
    
    speakers = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for group speakers"
    )

    members = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for group members"
    )
    
    outside_agents = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for outside agents associated with the group"
    )

    # Address fields
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)

    institution = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Institution or organization associated with the group"
    )

    links = ArrayField(
        models.URLField(max_length=500),
        blank=True,
        default=list,
        help_text="List of URLs associated with the group"
    )

    photos = ArrayField(
        models.URLField(max_length=500),
        blank=True,
        default=list,
        help_text="List of URLs for group photos"
    )

    pending_speakers = ArrayField(
        models.BigIntegerField(),
        blank=True,
        default=list,
        help_text="List of user IDs for pending speakers"
    )

    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def add_speaker(self, user_id):
        """Add speaker and update UserGroupParticipation"""
        if user_id not in self.speakers:
            self.speakers.append(user_id)
            self.save(update_fields=['speakers'])
            
            # Update or create participation record
            from .UserGroupParticipation import UserGroupParticipation
            participation, created = UserGroupParticipation.objects.get_or_create(user_id=user_id)
            if self.id not in participation.groups_as_speaker:
                participation.groups_as_speaker.append(self.id)
                participation.save(update_fields=['groups_as_speaker'])

    class Meta:
        db_table = 'event"."group'  # Schema-aware table name