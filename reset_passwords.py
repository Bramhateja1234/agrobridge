import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_platform.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

count = 0
for u in User.objects.all():
    u.set_password('Password')
    u.save()
    count += 1
print(f"Updated {count} users passwords to 'Password'.")
