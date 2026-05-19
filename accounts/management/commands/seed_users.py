from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the two private users into the database for high-performance syncing and calling'

    def handle(self, *args, **options):
        users_data = [
            {
                'email': 'user1@chatweb.com',
                'username': 'UserOne',
                'password': 'password123'
            },
            {
                'email': 'user2@chatweb.com',
                'username': 'UserTwo',
                'password': 'password123'
            }
        ]

        for u_data in users_data:
            user, created = User.objects.get_or_create(
                email=u_data['email'],
                defaults={'username': u_data['username']}
            )
            if created:
                user.set_password(u_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Successfully seeded user: {u_data['email']}"))
            else:
                self.stdout.write(self.style.WARNING(f"User {u_data['email']} already exists."))
