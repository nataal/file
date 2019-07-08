from django import forms

from .models import *
from django.db import transaction

from django.contrib.auth.models import Permission

from .utils import send_email, send_email_adhesion

from rolepermissions.roles import assign_role

from datetime import date
from django.utils import timezone

UtilisateurFormSet = forms.inlineformset_factory(Entite, Utilisateur, fields=('email', 'telephone'), can_delete=False,
                                                 extra=1)

OrganismeFormSet = forms.inlineformset_factory(Entite, OrganismeFormation, fields=('formations',), can_delete=False,
                                               extra=1)


class FormationForm(forms.ModelForm):
    """
    Formulaire d'ajout et d'édition d'une formation
    """
    organismes = forms.ModelMultipleChoiceField(queryset=OrganismeFormation.objects.all())

    class Meta:
        model = Formation
        fields = ('nom', 'contenu', 'validite', 'tav', 'organismes')

    def __init__(self, *args, **kwargs):
        super(FormationForm, self).__init__(*args, **kwargs)
        self.fields['organismes'].required = False

    def save(self, commit=True):
        super(FormationForm, self).save(commit)
        if hasattr(self.instance, 'formations_organismes'):
            self.instance.formations_organismes.all().delete()
        for org in self.cleaned_data['organismes']:
            FormationsOrganismes.objects.create(formation=self.instance, organisme_formation=org)

        return self.instance


class EntiteForm(forms.ModelForm):
    class Meta:
        model = Entite
        fields = ('raison_sociale', 'adresse')

    def __init__(self, *args, **kwargs):
        self.type = kwargs.pop('type')
        super(EntiteForm, self).__init__(*args, **kwargs)
        self.fields['email'] = forms.EmailField()
        self.fields['email'].required = True
        self.fields['telephone'] = forms.CharField(max_length=50)
        self.fields['telephone'].required = True

    @transaction.atomic
    def save(self, commit=True):
        self.instance.type = self.type
        super(EntiteForm, self).save(commit)
        entite = self.instance
        password = Utilisateur.get_dummy_password()
        email = self.cleaned_data.get('email', '')
        telephone = self.cleaned_data.get('telephone', '')
        if hasattr(entite, 'utilisateur'):
            utilisateur = entite.utilisateur
            utilisateur.email = email
            utilisateur.telephone = telephone
            utilisateur.save()
            assign_role(utilisateur, self.type)
        else:
            u = Utilisateur.objects.create_user(email=email, password=password, telephone=telephone, entite=entite)
            send_email(u, password)
            assign_role(u, self.type)

        return entite


class AdhesionForm(EntiteForm):
    @transaction.atomic
    def save(self, commit=True):
        self.instance.type = self.type
        super(EntiteForm, self).save(commit)
        entite = self.instance
        password = Utilisateur.get_dummy_password()
        email = self.cleaned_data.get('email', '')
        telephone = self.cleaned_data.get('telephone', '')
        u = Utilisateur.objects.create_user(email=email, password=password, telephone=telephone, entite=entite)
        send_email_adhesion(u, password)
        assign_role(u, self.type)

        return entite


class OrganismeFormationForm(forms.ModelForm):
    class Meta:
        model = Entite
        fields = ('raison_sociale', 'adresse')

    def __init__(self, *args, **kwargs):
        self.type = 'of'
        super(OrganismeFormationForm, self).__init__(*args, **kwargs)
        self.fields['exp_agreement'] = forms.DateField(input_formats=['%d/%m/%Y'])
        self.fields['exp_agreement'].required = True
        self.fields['email'] = forms.EmailField()
        self.fields['email'].required = True
        self.fields['telephone'] = forms.CharField(max_length=50)
        self.fields['telephone'].required = True
        self.fields['formations'] = forms.ModelMultipleChoiceField(queryset=Formation.objects.all())
        self.fields['formations'].required = False

    def add_email_error(self, email):
        if Utilisateur.objects.filter(email=email):
            return self.add_error('email', 'Cet email est déjà utilisé!')

    def clean(self):
        clean_data = super(OrganismeFormationForm, self).clean()
        email = clean_data['email']
        exists = Utilisateur.objects.filter(email=email)
        exp_agreement = clean_data['exp_agreement']
        now = timezone.now().date()
        if exists:
            if self.instance:
                if self.instance.utilisateur.email != email:
                    return self.add_error('email', 'Cet email est déjà utilisé!')
            else:
                return self.add_error('email', 'Cet email est déjà utilisé!')
        if now > exp_agreement:
            return self.add_error('exp_agreement', 'Cette date est dépassée!')
        return clean_data

    @transaction.atomic
    def save(self, commit=True):
        self.instance = super().save(commit)
        entite = self.instance
        email = self.cleaned_data.get('email', '')
        telephone = self.cleaned_data.get('telephone', '')
        formations = self.cleaned_data.get('formations', '')
        exp_agreement = self.cleaned_data.get('exp_agreement', '')
        if hasattr(entite, "utilisateur"):
            entite.utilisateur.email = email
            entite.utilisateur.telephone = telephone
            entite.utilisateur.save()
            of = entite.organisme_formation
            of.exp_agreement = exp_agreement
            of.save()
            if formations != of.formations.all():
                of.formations_organismes.all().delete()
                for formation in formations:
                    FormationsOrganismes.objects.create(formation=formation, organisme_formation=of)
        else:
            password = Utilisateur.get_dummy_password()
            user = Utilisateur.objects.create_user(email=email, telephone=telephone, password=password, entite=entite)
            assign_role(user, 'of')
            send_email(user, password)
            of = OrganismeFormation.objects.create(entite=entite, exp_agreement=exp_agreement)
            for formation in self.cleaned_data['formations']:
                FormationsOrganismes.objects.create(formation=formation, organisme_formation=of)

        return entite


class EntrepriseUtilForm(forms.ModelForm):
    class Meta:
        model = EntrepriseUtilisatrice
        fields = ('ca', 'contact_demarche', 'activite', 'directeur', 'effectif')

    def __init__(self, *args, **kwargs):
        super(EntrepriseUtilForm, self).__init__(*args, **kwargs)
        self.fields['intervenantes'] = forms.ModelMultipleChoiceField(queryset=EntrepriseIntervenante.objects.all())
        self.fields['intervenantes'].required = False
        if self.instance.pk:
            self.fields['intervenantes'].initial = self.instance.intervantes.all()
        self.fields['effectif'].required = False
        self.fields['directeur'].required = False
        self.fields['ca'].required = False

    def save(self, commit=True):
        self.instance = super(EntrepriseUtilForm, self).save(commit=True)
        if hasattr(self.instance, 'intervantes'):
            self.instance.intervantes.clear()
        for int in self.cleaned_data.get('intervenantes', ''):
            self.instance.intervantes.add(int)
        return self.instance


class EntrepriseInterForm(forms.ModelForm):
    class Meta:
        model = EntrepriseIntervenante
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EntrepriseInterForm, self).__init__(*args, **kwargs)
        self.fields['utilisatrices'].required = False


EntUtilFormSet = forms.inlineformset_factory(Entite, EntrepriseUtilisatrice, form=EntrepriseUtilForm, can_delete=False,
                                             extra=1)

EntInterFormSet = forms.inlineformset_factory(Entite, EntrepriseIntervenante, form=EntrepriseInterForm,
                                              can_delete=False, extra=1)


class IntervenantForm(forms.ModelForm):
    class Meta:
        model = Intervenant
        exclude = ('formations', 'num_gtis')


class FormationIntervenantForm(forms.ModelForm):
    class Meta:
        model = FormationIntervenant
        fields = ('formation', 'type',)


FormationIntervenantFormSet = forms.inlineformset_factory(Intervenant, FormationIntervenant,
                                                          form=FormationIntervenantForm,
                                                          fk_name='intervenant',
                                                          can_delete=True, extra=1)


class FormateurForm(forms.ModelForm):
    organismes = forms.ModelMultipleChoiceField(queryset=OrganismeFormation.objects.all())
    exp_agreement = forms.DateField(input_formats=['%d/%m/%Y'])

    class Meta:
        model = Formateur
        fields = ('nom', 'prenom', 'exp_agreement', 'organismes',)

    def __init__(self, *args, **kwargs):
        super(FormateurForm, self).__init__(*args, **kwargs)
        self.fields['organismes'].required = False

    def save(self, commit=True):
        super(FormateurForm, self).save()
        if hasattr(self.instance, 'formateursorganismes_set'):
            self.instance.formateursorganismes_set.all().delete()
        for organisme in self.cleaned_data['organismes']:
            self.instance.formateursorganismes_set.create(organisme=organisme)
        return self.instance


class FormateurFormOF(forms.ModelForm):
    class Meta:
        model = Formateur
        fields = ('nom', 'prenom',)

    def __init__(self, *args, **kwargs):
        self.organisme = kwargs.pop('organisme')
        super(FormateurFormOF, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance = super(FormateurFormOF, self).save(commit)
        FormateursOrganismes.objects.create(formateur=self.instance, organisme=self.organisme)
        return self.instance


class EventForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = '__all__'

    def clean_date(self):
        cleaned_data = self.clean()
        if cleaned_data['date'] < date.today():
            raise forms.ValidationError('Veuillez entrer une date valide!')

        return cleaned_data['date']


class DocumentForm(forms.ModelForm):
    class Meta:
        model = DocumentMase
        fields = '__all__'


class PermissionForm(forms.ModelForm):
    class Meta:
        model = Permission
        fields = '__all__'
