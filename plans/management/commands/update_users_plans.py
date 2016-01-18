from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from plans.models import UserPlan
from plans.signals import activate_user_plan


def user_signed_up_(sender, instance, created, **kwargs):
    """
    Whenever a user signs up, they should be added
    to the default plan.
    """
    activate_user_plan.send(sender=sender, user=instance)


class Command(BaseCommand):

    users = get_user_model()
    users = users.objects.all()
    for user in users:
        userplan, created = UserPlan.objects.get_or_create(user=user)
        if created:
            userplan.initialize()
