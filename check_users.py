import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agro_platform.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
print("Delivery Users:")
for u in User.objects.filter(role='delivery'):
    print(f"Email: {u.email} | Phone: {u.phone}")
