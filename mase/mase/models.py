from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.mail import send_mail
from django.contrib.auth.base_user import BaseUserManager
import uuid as uuid_lib
from django.conf import settings
from django.db.models.signals import post_save
from django.utils import timezone

import random, string
from django.utils.translation import gettext_lazy as _
import phonenumbers

# Create your models here.
SECTEURS = (
    ('TCMSM', 'Tuyauterie, chaudronnerie, mécanique, soudure, maintenance industrielle'),
    ('EEAR', 'Électricité, électromécanique, automatisme, régulation'),
    ('B', 'Bâtiment'),
    ('TP', 'Travaux publics'),
    ('IBE', 'Ingénierie, bureau d’études'),
    ('ECI', 'Échafaudage, calorifuge, isolation'),
    ('LM', 'Levage, montage'),
    ('CI', 'Contrôle, inspection'),
    ('NITCCDEV', 'Nettoyage industriel et tertiaire, curage, collecte de déchets, espaces verts'),
    ('LTL', 'Logistique, transports, location'),
    ('GS', 'Gardiennage, sécurité'),
    ('TT', 'Travail temporaire'),
    ('D', 'Divers')
)


class TimeStampModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UUID(models.Model):
    uuid = models.UUIDField(
        db_index=True,
        editable=False,
        default=uuid_lib.uuid4
    )

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('L\'email doit être renseigné!')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser, TimeStampModel):
    first_name = None
    last_name = None
    username = None
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=50, blank=True)
    entite = models.OneToOneField('Entite', related_name='utilisateur', null=True, on_delete=models.SET_NULL)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @staticmethod
    def get_dummy_password():
        """
        Renvoie un mot de passe aléatoire
        """
        return ''.join(random.sample(string.ascii_letters, 8))

    def __str__(self):
        return self.email

    def formater_phone(self):
        """
        Formate le numéro de téléphone dans un bon format
        """
        s = phonenumbers.parse(self.telephone, "SN")
        return phonenumbers.format_number(s, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.telephone:
                self.telephone = self.formater_phone()
            self.is_active = False
        return super(Utilisateur, self).save(*args, **kwargs)


class Entite(TimeStampModel, UUID):
    """
    Ce model représente les entreprises intervenante et utilisatrice mais aussi les organismes de formation
    """
    ENTREPRISE_INTERVENANTE = 'ei'
    ENTREPRISE_UTILISATRICE = 'eu'
    ORGANISME_FORMATION = 'of'
    TYPE = (
        (ENTREPRISE_INTERVENANTE, 'Entreprise intervenante'),
        (ENTREPRISE_UTILISATRICE, 'Entreprise utilisatrice'),
        (ORGANISME_FORMATION, 'Organisme de formation')
    )

    raison_sociale = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    type = models.CharField(max_length=2, choices=TYPE)

    def __str__(self):
        return self.raison_sociale


class OrganismeFormation(models.Model):
    """
    Ce model représente les organismes de formation
    """
    entite = models.OneToOneField(Entite, related_name='organisme_formation', on_delete=models.CASCADE)
    formations = models.ManyToManyField("Formation", through="FormationsOrganismes")
    formateurs = models.ManyToManyField('OrganismeFormation', through='FormateursOrganismes')
    exp_agreement = models.DateField()

    def __str__(self):
        return self.entite.raison_sociale


class Formation(TimeStampModel, UUID):
    nom = models.CharField(max_length=100, unique=True)
    contenu = models.TextField()
    validite = models.IntegerField()  # La validité de la formation en année
    tav = models.IntegerField()  # Le temps avant alerte en jours

    def __str__(self):
        return self.nom


class FormationsOrganismes(TimeStampModel):
    formation = models.ForeignKey(Formation, related_name="formations_organismes", on_delete=models.CASCADE)
    organisme_formation = models.ForeignKey(OrganismeFormation, related_name="formations_organismes", on_delete=models.CASCADE)

    def __str__(self):
        return self.formation.nom


class Formateur(TimeStampModel, UUID):
    """
    Ce model représente les formateurs d'un organisme de formation
    """
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    exp_agreement = models.DateField()

    def get_full_name(self):
        return '%s %s' % (self.prenom, self.nom)

    def __str__(self):
        return self.get_full_name()


class FormateursOrganismes(TimeStampModel):
    formateur = models.ForeignKey(Formateur, on_delete=models.CASCADE)
    organisme = models.ForeignKey(OrganismeFormation, on_delete=models.CASCADE)


class Entreprise(models.Model):
    activite = models.CharField(max_length=255, choices=SECTEURS)
    effectif = models.CharField(max_length=100, blank=True)
    ca = models.CharField(max_length=25, blank=True)
    directeur = models.CharField(max_length=100)
    contact_demarche = models.CharField(max_length=255)

    class Meta:
        abstract = True


class EntrepriseUtilisatrice(Entreprise):
    entite = models.OneToOneField(Entite, related_name='entreprise_utilisatrice', on_delete=models.CASCADE)

    def __str__(self):
        return self.entite.raison_sociale


class EntrepriseIntervenante(Entreprise):
    entite = models.OneToOneField(Entite, related_name='entreprise_intervenante', on_delete=models.CASCADE)
    organisation = models.CharField(max_length=255,
                                    blank=True)  # Quelle est l’organisation de votre société ? Direction / agence / établissement régional / local ?
    relations_etablissements = models.TextField(
                                    blank=True)  # Si plusieurs établissements opèrent dans le pays quelles sont les relations entre eux ?
    sous_traitants_activites = models.CharField(max_length=255,
                                                blank=True)  # Utilisez-vous régulièrement des sous-traitants ? Pour quelle part de vos activités ?
    intervention_industriels = models.CharField(max_length=255,
                                                blank=True)  # Sur quels sites industriels intervenez-vous habituellement ? précisez le nom des entreprises
    periode_audit = models.CharField(max_length=255, blank=True)
    demarche_management_qualite = models.BooleanField(default=False)
    demarche_iso = models.BooleanField(default=False)

    utilisatrices = models.ManyToManyField(EntrepriseUtilisatrice, related_name='intervantes')

    def __str__(self):
        return self.entite.raison_sociale


class Intervenant(models.Model):
    """
    Intervenant = Stagiaire => Ce sont les personnes qui reçoivent les certifications
    """
    MASCULIN = "H"
    FEMININ = "F"
    SEXES = (
        (MASCULIN, "Masculin"),
        (FEMININ, "Feminin")
    )

    #code = models.CharField(max_length=7, unique=True)
    num_gtis = models.CharField(max_length=100, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100)
    ei = models.ForeignKey(EntrepriseIntervenante, related_name='intervenants', on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos')
    formations = models.ManyToManyField(FormationsOrganismes, through="FormationIntervenant")

    def __str__(self):
        return self.num_gtis

    def save(self, *args, **kwargs):
        if not self.pk:
            now = timezone.now()
            self.num_gtis = "{}{}{}{}".format(now.day, now.month, now.year, now.strftime("%H:%M"))
        super(Intervenant, self).save(*args, **kwargs)


class FormationIntervenant(TimeStampModel, UUID):
    RECYCLAGE = 'r'
    INITIALE = 'i'
    TYPE_FORMATION = (
        (RECYCLAGE, 'Formation de recyclage'),
        (INITIALE, 'Formation initiale')
    )
    intervenant = models.ForeignKey(Intervenant, related_name='formations_intervenants', on_delete=models.CASCADE)
    formation = models.ForeignKey(FormationsOrganismes, related_name="formations_intervenants", on_delete=models.CASCADE)
    type = models.CharField(max_length=1, choices=TYPE_FORMATION)

    def __str__(self):
        return self.intervenant.code


class Evenement(TimeStampModel, UUID):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()

    def __str__(self):
        return self.nom


class DocumentMase(TimeStampModel, UUID):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    document = models.FileField(upload_to='documents')

    def __str__(self):
        return self.titre


#Signals connexion
#post_save.connect(receiver=email_message, sender=Utilisateur)