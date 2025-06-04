from django.db import models, connection
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from datetime import date
from geographies.models.geos import Country, State, District, Subdistrict, Village

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, gmail, first_name, last_name, password=None, **extra_fields):
        if not gmail:
            raise ValueError("Users must have a Gmail address")

        user = self.model(
            gmail=gmail,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, gmail, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(gmail, first_name, last_name, password, **extra_fields)

# Custom User Model with Global Sequence
class Petitioner(AbstractBaseUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    id = models.BigIntegerField(primary_key=True, editable=False)  # Manual ID assignment
    gmail = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    
    
    
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(editable=False)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    
    # Address details with foreign keys
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    subdistrict = models.ForeignKey(Subdistrict, on_delete=models.SET_NULL, null=True)
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True)

    is_online = models.BooleanField(default=False)
    
    # Required by Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'gmail'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        # Automatically calculate full name and age
        self.age = self.calculate_age()

        super().save(*args, **kwargs)

    def calculate_age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def __str__(self):
        return f"({self.first_name})"
    
    class Meta:
        db_table = 'userschema"."petitioner'
