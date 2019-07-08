from django.test import TestCase, Client
from django.urls import reverse_lazy

from .models import *

# Create your tests here.
class UserSimplePermissionTest(TestCase):
    """
    Test des permissions des utilisateurs simples : OF, EU et EI
    """
    fixtures = ['db.json']

    admin_views = ['ajouter_formation',
                   'ajouter_organisme',
                   'ajouter_formateur',
                   'ajouter_entreprise_interv',
                   'ajouter_intervenant',
                   'ajouter_entreprise_util',
                   'ajouter_event',
                   'ajouter_document']

    of_views = ['liste_organismes', 'mon_organisme', 'liste_formations', 'liste_entreprises_interv',
                'liste_entreprises_util', 'liste_formateurs', 'ajouter_formateur_of', 'liste_intervenants']

    eu_views = ['liste_organismes', 'liste_formations', 'liste_entreprises_interv',
                'liste_entreprises_util', 'mon_eu']

    ei_views = ['liste_organismes', 'liste_formations', 'liste_entreprises_interv',
                'liste_entreprises_util', 'mon_ei']

    def setUp(self):
        pass

    def requete(self, c, views, code):
        for url in map(reverse_lazy, views):
            response = c.get(str(url), follow=True)
            self.assertIsNone(response.redirect_chain)
            self.assertTrue(response.status_code, code)

    def init_requete(self, username, pwd, views, code):
        c = Client()
        log = c.login(username=username, password=pwd)
        self.assertTrue(log)
        self.requete(c, views, code)
        c.logout()

    def test_not_logged(self):
        c = Client()
        urls = map(reverse_lazy, self.ei_views+self.eu_views+self.of_views+self.admin_views)
        for url in urls:
            response = c.get(str(url), follow=True)
            self.assertTrue(hasattr(response, 'redirect_chain'))
            self.assertEqual(len(response.redirect_chain), 1)
            tpl, *none = response.redirect_chain
            URL, status_code = tpl
            self.assertTrue(str(reverse_lazy('connexion')) in URL)
            self.assertEqual(status_code, 302)

    def test_of_authorized_access(self):
        self.init_requete('jlsemedo@sunuhope.com', 'iuJFvYyA', self.of_views, 200)

    def test_eu_authorized_access(self):
        self.init_requete('diambarsmobile@gmail.com', 'XZwHuTnc', self.eu_views, 200)

    def test_ei_authorized_access(self):
        self.init_requete('aristide.semedo@gmail.com', 'lThWOtVs', self.ei_views, 200)

    def test_of_unauth_access(self):
        c = Client()
        for username, password in [("jlsemedo@sunuhope.com", "iuJFvYyA") , ("aristide.semedo@gmail.com", "lThWOtVs"), ("diambarsmobile@gmail.com", "XZwHuTnc")]:
            c.login(username = username, password = password)
            for url in map(reverse_lazy, self.admin_views):
                response = c.get(str(url))
                self.assertRedirects(response, '/login/?next={}'.format(str(url)))


    # def test_eu_unauth_access(self):
    #     self.requete(self.admin_views, 404)
    #
    # def test_ei_unauth_access(self):
    #     self.requete(self.admin_views, 404)


class AdminPermissionTest(TestCase):
    """
    Test des permissions des administrateurs
    """
    NotImplemented


class OrganismeFormationTest(TestCase):
    """
    Test sur les organismes de formation
    """

    def setUp(self):
        pass
