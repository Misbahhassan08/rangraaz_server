from django.core.management.base import BaseCommand

from rangraaz.models import Customer


TEST_USERS = [
    {
        "name": "Test Admin",
        "phone": "3000000001",
        "password": "admin123",
        "address": "Rang Raaz Studio",
        "role": "admin",
        "email": "admin@test.rangraaz.local",
    },
    {
        "name": "Test Customer",
        "phone": "3000000002",
        "password": "customer123",
        "address": "Customer Test Address",
        "role": "customer",
        "email": "customer@test.rangraaz.local",
    },
    {
        "name": "Google Test Customer",
        "phone": "3000000003",
        "password": "GOOGLE",
        "address": "Google OAuth Test Address",
        "role": "customer",
        "email": "google.customer@test.rangraaz.local",
    },
]


class Command(BaseCommand):
    help = "Create or update repeatable local test users for Rang Raaz."

    def handle(self, *args, **options):
        for user_data in TEST_USERS:
            phone = user_data["phone"]
            user, created = Customer.objects.update_or_create(
                phone=phone,
                defaults=user_data,
            )
            status = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{status}: {user.name} | phone={user.phone} | "
                    f"password={user.password} | role={user.role}"
                )
            )
