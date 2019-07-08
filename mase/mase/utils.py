from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from django.conf import settings

from .models import Utilisateur

from django.utils import timezone

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Cette classe nous permet de générer une URL unique pour l'activation des comptes
    """
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )


def send_email(user, pwd):
    """
    Fonction permettant l'envoi de mail
    """
    #current_site = get_current_site(request)
    current_site = "www.mase.sn"
    subject = 'Activation de votre compte MASE'
    message_ = render_to_string('mase/account_activation_email.html', {
        'user': user,
        'domain': current_site,
        'password': pwd,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
        'token': AccountActivationTokenGenerator().make_token(user),
    })
    # On envoie un mail à l'utilisateur pour activation
    user.email_user(subject, message_, settings.EMAIL_MAIN)


def send_email_adhesion(user, pwd):
    """
    Fonction permettant l'envoi de mail à une d'adhesion à MASE
    """
    current_site = "www.mase.sn"
    subject1 = 'Activation de votre compte MASE'
    message_soumissionnaire = render_to_string('mase/account_adhesion_email.html', {
        'user': user,
        'domain': current_site,
        'password': pwd
    })
    subject2 = 'Nouvelle demande d\'admission à MASE'
    message_administrateur = render_to_string('mase/demande_adhesion_email.html', {
        'user': user,
        'domain': current_site,
        'password': pwd
    })
    # On envoie un mail à l'utilisateur pour activation
    user.email_user(subject1, message_soumissionnaire, settings.EMAIL_MAIN)
    # On envoie un mail à l'administrateur pour information
    admin = Utilisateur.objects.filter(is_superuser=1).first()
    admin.email_user(subject2, message_administrateur, settings.EMAIL_MAIN)

def generate_numgtis(ei, stagiaire):
    #Les num_gtis sont générés selon le modèle suivant : {id_entreprise_intervenante}-{id_stagiaire}-{ddmmyyy}
    now = timezone.now()
    ymd = "{}{}{}".format(now.day, now.month, now.year)
    return "{}-{}-{}".format(ei, stagiaire, ymd)