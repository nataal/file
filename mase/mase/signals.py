from django.apps import apps
from django.dispatch import receiver
from django.db.models.signals import post_save

from .utils import send_email, generate_numgtis
from .models import Intervenant


# def email_message(sender, instance, created, **kwargs):
#     UserModel = apps.get_model(app_label='mase', model_name='Utilisateur')
#     send_email(UserModel.objects.get(pk=instance.pk), pwd="Temps")


@receiver(post_save, sender=Intervenant)
def save_numgtis(sender, instance, **kwargs):
    print(instance)
    if kwargs['created']:
        instance.num_gtis = generate_numgtis(instance.ei.pk, instance.pk)
        instance.save()