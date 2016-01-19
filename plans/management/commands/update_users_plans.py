from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from plans.models import UserPlan


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = get_user_model()
        users = users.objects.all()
        for user in users:
            userplan, created = UserPlan.objects.get_or_create(user=user)
            if created:
                userplan.initialize()
