import random
from faker import Faker
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
from django.utils import timezone
from users.models import Petitioner

fake = Faker('en_IN')

def create_live_user(villages, existing_users):
    """Create single user with realistic live data"""
    village = random.choice(villages)
    village.online_population += 1
    village.save(update_fields=['online_population'])
    
    # Generate unique ID
    village_id_str = str(village.id)[-9:].zfill(9)
    pop_code = str(village.online_population).zfill(5)
    generated_id = int(village_id_str + pop_code)
    
    # Ensure unique email
    email_exists = True
    while email_exists:
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}{generated_id}@live.example.com"
        email_exists = Petitioner.objects.filter(gmail=email).exists()
    
    return Petitioner.objects.create(
        id=generated_id,
        gmail=email,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
        gender=random.choice(['M', 'F', 'O']),
        country=village.subdistrict.district.state.country,
        state=village.subdistrict.district.state,
        district=village.subdistrict.district,
        subdistrict=village.subdistrict,
        village=village,
        password=make_password("live_pass123"),
        date_joined=timezone.now()
    )