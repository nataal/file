from django.shortcuts import render, redirect, render_to_response
from django.views.generic import CreateView, DetailView, UpdateView, ListView, DeleteView, TemplateView
from django.views import View
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import login
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import *
from .forms import *
from .utils import AccountActivationTokenGenerator

from rolepermissions.roles import assign_role
from rolepermissions.mixins import HasPermissionsMixin
from rolepermissions.decorators import has_permission_decorator

from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape

# Create your views here.

def home(request):
    formations = Formation.objects.all().count()
    eu = EntrepriseUtilisatrice.objects.all().count()
    ei = EntrepriseIntervenante.objects.all().count()
    of = OrganismeFormation.objects.all().count()
    events = Evenement.objects.filter(date__gt=timezone.now().date())[:3]
    context = {
        'eu' : eu,
        'ei' : ei,
        'of' : of,
        'formations' : formations,
        'events' : events
    }
    return render(request, 'mase/accueil.html', context)


def presentation(request):
    return render(request, 'mase/presentation_mase.html')


def veille_reglementaire(request):
    return render(request, 'mase/veille_reglementaire.html')


def cabinets_audit(request):
    return render(request, 'mase/cabinets_audit.html')


def centres_formations(request):
    of = OrganismeFormation.objects.all()
    return render(request, 'mase/centres_formations.html', {'of' : of})


def historique(request):
    return render(request, 'mase/historique.html')


def certification(request):
    return render(request, 'mase/certification.html')


def maseSenegal(request):
    return render(request, 'mase/presentation_mase_senegal.html')


#def adhesions(request):
    #return render(request, 'mase/adhesions.html')

class AdhesionCreate(TemplateView):
    template_name = 'mase/adhesions.html'
    success_url = reverse_lazy('adhesions')

    def get(self, request, *args, **kwargs):
        eu_form = AdhesionForm(prefix="eu", type="eu")
        eu_formset = EntUtilFormSet(prefix="eu")
        ei_form = AdhesionForm(prefix="ei", type="ei")
        ei_formset = EntInterFormSet(prefix="ei")
        eu = Entite.objects.filter(type='eu').order_by('raison_sociale')
        ei = Entite.objects.filter(type='ei').order_by('raison_sociale')
        context = {
            'eu_form': eu_form,
            'eu_formset': eu_formset,
            'ei_form' : ei_form,
            'ei_formset': ei_formset,
            'ei' : ei,
            'eu' : eu
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        eu_form = AdhesionForm(request.POST, prefix="eu", type="eu")
        eu_formset = EntUtilFormSet(request.POST, prefix="eu")
        ei_form = AdhesionForm(request.POST, prefix="ei", type="ei")
        ei_formset = EntInterFormSet(request.POST, prefix="ei")
        if eu_form.is_valid():
            entite = eu_form.save()
            if eu_formset.is_valid():
                eu_formset.instance = entite
                eu_formset.save()
        elif ei_form.is_valid():
            entite = ei_form.save()
            if ei_formset.is_valid():
                ei_formset.instance = entite
                ei_formset.save()
        else:
            context = {
                'eu_form': eu_form,
                'eu_formset': eu_formset,
                'ei_form': ei_form,
                'ei_formset': ei_formset
            }
            messages.warning(request, "Veuillez corriger les erreurs svp!")
            return self.render_to_response(context)
        return HttpResponseRedirect(self.success_url)


def activites(request):
    object_list = Evenement.objects.all().order_by('-date')
    return render(request, 'mase/activites.html', {'object_list' : object_list})


def contact(request):
    return render(request, 'mase/contact.html')


def activation_compte(request, uidb64, token):
    try:
        uid = str(urlsafe_base64_decode(uidb64).decode())
        user = Utilisateur.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None
    if user is not None and AccountActivationTokenGenerator().check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'mase/success.html')
    else:
        return render(request, 'mase/failure.html')


def desactiver_entite(request, pk):
    try:
        entite = Entite.objects.get(pk=pk)
    except:
        messages.warning(request, 'Entité inexistante')
        return redirect('liste_entites')
    if request.POST:
        for utilisateur in entite.utilisateurs.all():
            utilisateur.is_active = False
            utilisateur.save()
    return render(request, 'mase/entite_desactiver_confirm.html', {'entite': entite})


def reactiver_entite(request, pk):
    try:
        entite = Entite.objects.get(pk=pk)
    except:
        messages.warning(request, 'Entité inexistante')
        return redirect('liste_entites')
    if request.POST:
        for utilisateur in entite.utilisateurs.all():
            utilisateur.is_active = True
            utilisateur.save()
    return render(request, 'mase/entite_reactiver_confirm.html', {'entite': entite})


class MyLoginRequiredMixin(LoginRequiredMixin):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'


class FormInvalidMixin:
    def form_invalid(self, form):
        messages.warning(self.request, "Veuillez corriger les erreurs svp!")
        return super().form_invalid(form)


class FormationList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_formations'
    model = Formation
    template_name = 'mase/formation_list.html'


class FormationCreate(MyLoginRequiredMixin, HasPermissionsMixin, CreateView):
    required_permission = 'ajouter_une_formation'
    form_class = FormationForm
    template_name = 'mase/formation_form.html'
    success_url = reverse_lazy('liste_formations')


class FormationDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'ajouter_une_formation'
    model = Formation
    template_name = 'mase/formation_detail.html'
    slug_field = 'uuid'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['intervenants'] = Intervenant.objects.filter(formations__in=self.object.formations_organismes.all())
        return data


class FormationUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    required_permission = 'modifier_une_formation'
    form_class = FormationForm
    model = Formation
    template_name = 'mase/formation_update.html'
    slug_field = 'uuid'

    def get_form_kwargs(self):
        kwargs = super(FormationUpdate, self).get_form_kwargs()
        kwargs['initial'] = {
            'organismes': self.object.organismeformation_set.all()
        }
        return kwargs

    def get_success_url(self):
        return reverse('detail_formation', kwargs={'slug': self.object.uuid})


class FormationDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'suppri'
    model = Formation
    template_name = 'mase/formation_delete_confirm.html'
    success_url = reverse_lazy('liste_formations')
    slug_field = 'uuid'


class OrganismeFormationList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_OF'
    model = OrganismeFormation
    fields = ['nom', 'formations']
    template_name = 'mase/organisme_list.html'

    def get_queryset(self):
        return super(OrganismeFormationList, self).get_queryset().select_related('entite')


class OrganismeFormationCreate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, CreateView):
    required_permission = 'ajouter_un_OF'
    form_class = OrganismeFormationForm
    template_name = 'mase/organisme_form.html'
    success_url = reverse_lazy('liste_organismes')

    def form_valid(self, form):
        messages.success(self.request, 'Enregistrement reussi')
        return super(OrganismeFormationCreate, self).form_valid(form)


class OrganismeFormationDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'lister_les_OF'
    model = OrganismeFormation
    template_name = 'mase/organisme_detail.html'
    slug_field = 'entite__uuid'


class MonOrganismeFormation(OrganismeFormationDetail):
    def get_object(self, queryset=None):
        return self.request.user.entite.organisme_formation

class OrganismeFormationUpdate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, UpdateView):
    required_permission = 'modifier_un_OF'
    model = Entite
    template_name = 'mase/organisme_update.html'
    slug_field = 'uuid'
    form_class = OrganismeFormationForm

    def get_success_url(self):
        return reverse('detail_organisme', kwargs={'slug': self.object.uuid})

    def get_form_kwargs(self):
        kwargs = super(OrganismeFormationUpdate, self).get_form_kwargs()
        kwargs['initial'] = {
            'email': self.object.utilisateur.email,
            'telephone': self.object.utilisateur.telephone,
            'formations': self.object.organisme_formation.formations.all(),
            'exp_agreement' : self.object.organisme_formation.exp_agreement
        }
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Enregistrement reussi")
        return super(OrganismeFormationUpdate, self).form_valid(form)


class ModifierMonOrganismeFormation(OrganismeFormationUpdate):
    def get_object(self, queryset=None):
        return self.request.user.entite.organisme_formation


class OrganismeFormationDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'supprimer_un_OF'
    model = Entite
    template_name = 'mase/organisme_delete_confirm.html'
    success_url = reverse_lazy('liste_organismes')
    slug_field = 'uuid'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.utilisateur.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)


@has_permission_decorator('desactiver_un_OF')
def desactiver_of(request, pk):
    """
    Désactiver un organisme de formation revient à désactiver tous ses utilisateurs 
    """
    try:
        organisme = OrganismeFormation.objects.get(pk=pk)
        utilisateurs = organisme.entite.utilisateurs.all()
        for utilisateur in utilisateurs:
            utilisateur.is_active = False
            utilisateur.save()
        messages.success(request, 'Organisme désactivé!')
    except ObjectDoesNotExist:
        messages.warning(request, 'Organisme non trouvé!')
    finally:
        return redirect('liste_organismes')


@has_permission_decorator('activer_un_OF')
def activer_of(request, pk):
    """
    Activer un organisme de formation revient à activer tous ses utilisateurs 
    """
    try:
        organisme = OrganismeFormation.objects.get(pk=pk)
        utilisateurs = organisme.entite.utilisateurs.all()
        for utilisateur in utilisateurs:
            utilisateur.is_active = True
            utilisateur.save()
        messages.success(request, 'Organisme activé!')
    except ObjectDoesNotExist:
        messages.warning(request, 'Organisme non trouvé!')
    finally:
        return redirect('liste_organismes')


class FormateurCreate(MyLoginRequiredMixin, HasPermissionsMixin, CreateView):
    required_permission = 'ajouter_un_formateur'
    form_class = FormateurForm
    success_url = reverse_lazy('liste_formateurs')
    template_name = 'mase/formateur_form.html'


class FormateurCreateOF(FormateurCreate):
    required_permission = 'ajouter_un_formateur_of'
    form_class = FormateurFormOF
    template_name = 'mase/formateur_form_of.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisme"] = self.request.user.entite.organisme_formation
        return kwargs


class FormateurList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_formateurs'
    model = Formateur
    template_name = 'mase/formateur_list.html'


class FormateurDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'lister_les_formateurs'
    model = Formateur
    template_name = 'mase/formateur_detail.html'
    slug_field = 'uuid'


class FormateurUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    required_permission = 'modifier_un_formateur'
    form_class = FormateurForm
    template_name = 'mase/formateur_update.html'
    slug_field = 'uuid'
    model = Formateur

    def get_success_url(self):
        return reverse('detail_formateur', kwargs={'slug': self.object.uuid})


class FormateurDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'supprimer_un_formateur'
    model = Formateur
    template_name = 'mase/formateur_delete_confirm.html'
    slug_field = 'uuid'
    success_url = reverse_lazy('liste_formateurs')


class EntrepriseIntList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_EI'
    model = Entite
    template_name = 'mase/entreprise_inter_list.html'
    queryset = Entite.objects.filter(type='ei')


class EntrepriseIntCreate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, CreateView):
    required_permission = 'ajouter_une_EI'
    form_class = EntiteForm
    template_name = 'mase/entreprise_inter_form.html'
    success_url = reverse_lazy('liste_entreprises_interv')

    def get_form_kwargs(self):
        kwargs = super(EntrepriseIntCreate, self).get_form_kwargs()
        kwargs['type'] = 'ei'
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['entreprise_inter'] = EntInterFormSet(self.request.POST)
        else:
            data['entreprise_inter'] = EntInterFormSet()
        return data

    @transaction.atomic
    def form_valid(self, form):
        data = self.get_context_data()
        entreprise_inter = data['entreprise_inter']



        if entreprise_inter.is_valid():
            # on enregistre l'entité

            self.object = form.save()

            # enfin on crée l'entreprise intervenante
            entreprise_inter.instance = self.object
            entreprise_inter.save()
            messages.success(self.request, 'Entreprise intervenante créée')

            return HttpResponseRedirect(self.get_success_url())

        else:
            messages.warning(self.request, 'Veuillez remplir les champs restants')
            return self.form_invalid(form)


class EntrepriseIntUpdate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, UpdateView):
    required_permission = 'modifier_une_EI'
    model = Entite
    form_class = EntiteForm
    slug_field = 'uuid'
    template_name = 'mase/entreprise_inter_update.html'

    def get_success_url(self):
        return reverse('detail_entreprise_interv', kwargs={'slug': self.object.uuid})

    def get_form_kwargs(self):
        kwargs = super(EntrepriseIntUpdate, self).get_form_kwargs()
        kwargs['type'] = 'ei'
        kwargs['initial'] = {
            'email': self.object.utilisateur.email,
            'telephone': self.object.utilisateur.telephone
        }
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['entreprise_inter'] = EntInterFormSet(self.request.POST, instance=self.object)
        else:
            data['entreprise_inter'] = EntInterFormSet(instance=self.object)

        return data

    @transaction.atomic
    def form_valid(self, form):
        data = self.get_context_data()
        self.object = form.save()

        entreprise_inter = data['entreprise_inter']
        entreprise_inter.instance = self.object

        if entreprise_inter.is_valid():
            entreprise_inter.save()
            messages.success(self.request, 'Modification enregistrée')
            return HttpResponseRedirect(self.get_success_url())
        else:
            print(entreprise_inter.errors)
            messages.warning(self.request, 'Veuillez remplir les champs restants')
            return self.form_invalid(form)


class ModifierMonEI(EntrepriseIntUpdate):
    required_permission = 'afficher_mon_EI'
    def get_object(self, queryset=None):
        return self.request.user.entite


class EntrepriseIntDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'lister_les_EI'
    model = Entite
    template_name = 'mase/entreprise_inter_detail.html'
    slug_field = 'uuid'


class MonEI(EntrepriseIntDetail):
    required_permission = 'afficher_mon_EI'
    def get_object(self, queryset=None):
        return self.request.user.entite


class EntrepriseIntDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'supprimer_une_EI'
    model = Entite
    template_name = 'mase/entreprise_inter_delete_confirm.html'
    success_url = reverse_lazy('liste_entreprises_interv')
    slug_field = 'uuid'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.utilisateur.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class IntervenantCreate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, CreateView):
    required_permission = 'ajouter_un_intervenant'
    form_class = IntervenantForm
    template_name = 'mase/intervenant_form.html'
    success_url = reverse_lazy('liste_intervenants')


class IntervenantDetail(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, DetailView):
    required_permission = 'ajouter_un_intervenant'
    model = Intervenant
    template_name = 'mase/intervenant_detail.html'
    slug_field = 'num_gtis'


class IntervenantList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_intervenants'
    model = Intervenant
    template_name = 'mase/intervenant_list.html'


class IntervenantUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    required_permission = 'modifier_un_intervenant'
    model = Intervenant
    fields = ['nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'ei', 'photo']
    template_name = 'mase/intervenant_update.html'
    success_url = reverse_lazy('liste_intervenants')
    slug_field = 'num_gtis'

    def get_context_data(self, **kwargs):
        data = super(IntervenantUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['formation_intervenant'] = FormationIntervenantFormSet(self.request.POST, instance=self.object)
        else:
            data['formation_intervenant'] = FormationIntervenantFormSet()
        return data

    def form_valid(self, form):
        self.object = form.save()
        data = self.get_context_data()
        formation_intervenant = data['formation_intervenant']
        formation_intervenant.instance = self.object
        if formation_intervenant.is_valid():
            formation_intervenant.save()
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form):
        print(form.errors)
        return super(IntervenantUpdate, self).form_invalid(form)


class IntervenantDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'supprimer_un_intervenant'
    model = Intervenant
    template_name = 'mase/intervenant_confirm_delete.html'
    success_url = reverse_lazy('liste_intervenants')
    slug_field = 'code'


class EntrepriseUtilCreate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, CreateView):
    required_permission = 'ajouter_une_EU'
    form_class = EntiteForm
    template_name = 'mase/entreprise_util_form.html'
    success_url = reverse_lazy('liste_entreprises_util')

    def get_form_kwargs(self):
        kwargs = super(EntrepriseUtilCreate, self).get_form_kwargs()
        kwargs['type'] = 'eu'
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['entreprise_util'] = EntUtilFormSet(self.request.POST)
        else:
            data['entreprise_util'] = EntUtilFormSet()
        return data

    @transaction.atomic
    def form_valid(self, form):
        data = self.get_context_data()
        entreprise_util = data['entreprise_util']

        if entreprise_util.is_valid():
            # on enregistre l'entité
            self.object = form.save()

            # enfin on crée l'entreprise intervenante
            entreprise_util.instance = self.object

            entreprise_util.save()
            messages.success(self.request, 'Entreprise utilisatrice créée')

            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.warning(self.request, 'Veuillez remplir les champs restants')
            return self.form_invalid(form)


class EntrepriseUtilList(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_EU'
    model = Entite
    template_name = 'mase/entreprise_util_list.html'
    queryset = Entite.objects.filter(type='eu')


class EntrepriseUtilDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'lister_les_EU'
    model = Entite
    slug_field = 'uuid'
    template_name = 'mase/entreprise_util_detail.html'


class MonEU(EntrepriseUtilDetail):
    required_permission = 'afficher_mon_EU'
    def get_object(self, queryset=None):
        return self.request.user.entite


class EntrepriseUtilUpdate(MyLoginRequiredMixin, HasPermissionsMixin, FormInvalidMixin, UpdateView):
    required_permission = 'modifier_une_EU'
    form_class = EntiteForm
    model = Entite
    slug_field = 'uuid'
    template_name = 'mase/entreprise_util_update.html'

    def get_success_url(self):
        return reverse('detail_entreprise_util', kwargs={'slug': self.object.uuid})

    def get_form_kwargs(self):
        kwargs = super(EntrepriseUtilUpdate, self).get_form_kwargs()
        kwargs['type'] = 'eu'
        kwargs['initial'] = {
            'email': self.object.utilisateur.email,
            'telephone': self.object.utilisateur.telephone,
        }
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(EntrepriseUtilUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            data['entreprise_util'] = EntUtilFormSet(self.request.POST, instance=self.object)
        else:
            data['entreprise_util'] = EntUtilFormSet(instance=self.object)
        return data

    @transaction.atomic
    def form_valid(self, form):
        data = self.get_context_data()
        entreprise_util = data['entreprise_util']

        self.object = form.save()
        entreprise_util.instance = self.object
        if entreprise_util.is_valid():
            entreprise_util.save()
            messages.success(self.request, "Modification effectuée avec succès!")

            return HttpResponseRedirect(self.get_success_url())
        else:
            print(entreprise_util.errors)
            messages.warning(self.request, 'Veuillez remplir les champs restants')
            return self.form_invalid(form)


class ModifierMonEU(EntrepriseUtilUpdate):
    required_permission = 'afficher_mon_EU'
    def get_object(self, queryset=None):
        return self.request.user.entite

class EntrepriseUtilDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'supprimer_une_EU'
    model = Entite
    template_name = 'mase/entreprise_util_confirm_delete.html'
    success_url = reverse_lazy('liste_entreprises_util')
    slug_field = 'uuid'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.utilisateur.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class DesactivationMixin:
    @property
    def success_url(self):
        return NotImplemented

    def get(self, request, *args, **kwargs):
        entite = get_object_or_404(Entite, slug=kwargs['uuid'])
        utilisateur = entite.utilisateur
        utilisateur.is_active = not utilisateur.is_active
        utilisateur.save()
        messages.success(request, "Modification enregistrée")
        return HttpResponseRedirect(self.success_url)


class EntrepriseUtilActivation(MyLoginRequiredMixin, HasPermissionsMixin, DesactivationMixin, View):
    success_url = reverse_lazy('liste_entreprises_util')
    required_permission = 'activer_une_EU'


class EntrepriseInterActivation(MyLoginRequiredMixin, HasPermissionsMixin, DesactivationMixin, View):
    success_url = reverse_lazy('liste_entreprises_interv')
    required_permission = 'activer_une_EI'


class EvenementCreate(MyLoginRequiredMixin, HasPermissionsMixin, CreateView):
    required_permission = 'gerer_les_events'
    form_class = EventForm
    template_name = 'mase/event_form.html'
    success_url = reverse_lazy('liste_events')


class EvenementListe(MyLoginRequiredMixin, ListView):
    template_name = 'mase/event_list.html'
    model = Evenement

    def get_queryset(self):
        return Evenement.objects.all().order_by('-date')


class EvenementDetail(MyLoginRequiredMixin, HasPermissionsMixin, DetailView):
    required_permission = 'gerer_les_events'
    slug_field = 'uuid'
    model = Evenement
    template_name = 'mase/event_detail.html'



class EvenementUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    required_permission = 'gerer_les_events'
    model = Evenement
    form_class = EventForm
    slug_field = 'uuid'
    template_name = 'mase/event_update.html'

    def get_success_url(self):
        return reverse('detail_event', kwargs={'slug' : self.object.uuid})


class EvenementDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'gerer_les_events'
    model = Evenement
    slug_field = 'uuid'
    template_name = 'mase/event_delete_confirm.html'
    success_url = reverse_lazy('liste_events')


class DocumentListe(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_documents'
    model = DocumentMase
    template_name = 'mase/document_list.html'

    def get_queryset(self):
        return super(DocumentListe, self).get_queryset().order_by('titre')

class DocumentAdminListe(DocumentListe):
    template_name = 'mase/document_list_admin.html'
    required_permission = 'gerer_les_documents'


class DocumentCreate(MyLoginRequiredMixin, HasPermissionsMixin, CreateView):
    required_permission = 'gerer_les_documents'
    form_class = DocumentForm
    model = DocumentMase
    template_name = 'mase/document_form.html'
    success_url = reverse_lazy('liste_documents')


class DocumentUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    required_permission = 'gerer_les_documents'
    form_class = DocumentForm
    model = DocumentMase
    template_name = 'mase/document_update.html'
    slug_field = 'uuid'

    def get_success_url(self):
        return reverse_lazy('document_detail', kwargs={'slug' : self.object.uuid})

class DocumentDetail(MyLoginRequiredMixin, DetailView):
    template_name = 'mase/document_detail.html'
    slug_field = 'uuid'
    model = DocumentMase


class DocumentDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    required_permission = 'gerer_les_documents'
    model = DocumentMase
    template_name = 'mase/document_delete_confirm.html'
    slug_field = 'uuid'
    success_url = reverse_lazy('liste_documents')


class UtilisateurListe(MyLoginRequiredMixin, HasPermissionsMixin, ListView):
    required_permission = 'lister_les_users'
    model = Utilisateur
    template_name = 'mase/utilisateur_liste.html'

    def get_queryset(self):
        return super(UtilisateurListe, self).get_queryset().order_by('-email')


class UtilisateurUpdate(MyLoginRequiredMixin, HasPermissionsMixin, UpdateView):
    pass


class UtilisateurDelete(MyLoginRequiredMixin, HasPermissionsMixin, DeleteView):
    template_name = 'mase/supprimer_utilisateur_confirm.html'
    model = Utilisateur

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = reverse('liste_utilisateurs')
        a = self.object
        self.object.delete()
        if hasattr(a, 'entite'):
            entite = a.entite
            entite.delete()
        return HttpResponseRedirect(success_url)



class ActivationUtilisateur(MyLoginRequiredMixin, HasPermissionsMixin, View):
    required_permission = 'lister_les_users'
    def get(self, request, *args, **kwargs):
        utilisateur = get_object_or_404(Utilisateur, pk=kwargs['pk'])
        utilisateur.is_active = not utilisateur.is_active
        utilisateur.save()
        messages.success(request, "Utilisateur modifié")
        return redirect('liste_utilisateurs')


class MonProfil(MyLoginRequiredMixin, DetailView):
    model = Utilisateur
    template_name = 'mase/profile.html'

    def get_object(self, queryset=None):
        return self.request.user


class AjaxUtilisateur(BaseDatatableView):
    model = Utilisateur
    columns = ['email', 'structure', 'telephone', 'created', 'role', 'is_active', 'actions']
    order_columns = ['email', '', 'telephone', 'created', '', 'is_active', '']
    max_display_length = 500

    def get_group(self, name):
        return {
            'of' : 'Organisme de Formation',
            'eu' : 'Entreprise utilisatrice',
            'ei' : 'Entreprise intervenante',
            'admin' : 'Administrateur'
        }.get(name, '')

    def get_initial_queryset(self):
        return super(AjaxUtilisateur, self).get_initial_queryset().order_by('entite')

    def render_column(self, row, column):
        if column == 'structure':
            return escape('{}'.format(row.entite.raison_sociale if hasattr(row.entite, 'raison_sociale') else ''))
        if column == 'role':
            r = ''
            for role in row.groups.all():
                r += self.get_group(role.name)
            return escape('{}'.format(r))
        if column == 'is_active':
            return escape('{}'.format('Actif' if row.is_active else 'Inactif'))
        if column == 'created':
            return row.created.strftime('%d %m %Y')
        if column == 'actions':
            action = '<a href="{}" title="Supprimer"><span class="fa fa-trash"></span></a>'.format(reverse('supprimer_utilisateur', kwargs={'pk' : row.pk}))
            if row.is_active:
                action+= ' <a href="{}" title="Desactiver"><span class="fa fa-ban"></span></a>'.format(reverse('activation_utilisateur', kwargs={'pk' : row.pk}))
            else:
                action+=' <a href="{}" title="Activer"><span class="fa fa-check"></span></a>'.format(reverse('activation_utilisateur', kwargs={'pk' : row.pk}))
            return action
        else:
            return super(AjaxUtilisateur, self).render_column(row, column)


    def filter_queryset(self, qs):
        search = self.request.GET.get(u'search[value]', None)
        if search:
            qs = qs.filter(email__icontains=search)
        return qs

