from rolepermissions.roles import AbstractUserRole

class Admin(AbstractUserRole):
    available_permissions = {
        'lister_les_OF': True,
        'ajouter_un_OF': True,
        'modifier_un_OF': True,
        'supprimer_un_OF': True,
        'activer_un_OF' : True,
        'desactiver_un_OF' : True,
        'lister_les_formations': True,
        'ajouter_une_formation': True,
        'modifier_une_formation': True,
        'supprimer_une_formation': True,
        'lister_les_formateurs': True,
        'ajouter_un_formateur': True,
        'ajouter_un_formateur_of': True,
        'modifier_un_formateur': True,
        'supprimer_un_formateur': True,
        'lister_les_intervenants': True,
        'ajouter_un_intervenant': True,
        'modifier_un_intervenant': True,
        'supprimer_un_intervenant': True,
        'lister_les_EU': True,
        'ajouter_une_EU' : True,
        'modifier_une_EU': True,
        'supprimer_une_EU': True,
        'activer_une_EU': True,
        'lister_les_EI': True,
        'ajouter_une_EI' : True,
        'modifier_une_EI': True,
        'supprimer_une_EI': True,
        'activer_une_EI': True,
        'stats': True,
        'download_stats': True,
        'gerer_les_events': True,
        'gerer_les_documents': True,
        'lister_les_documents' : True,
        'lister_les_users': True,
        'add_edit_act_desact_user' : True
    }

class OF(AbstractUserRole):
    available_permissions = {
        'lister_les_OF': True,
        'afficher_mon_organisme' : True,
        'lister_les_formations': True,
        'lister_les_formateurs': True,
        'ajouter_un_formateur_of' : False,
        'lister_les_intervenants': True,
        'lister_les_EU': True,
        'lister_les_EI': True,
        'lister_les_documents': True,
        'modifier_un_intervenant' : True,
    }


class EU(AbstractUserRole):
    available_permissions = {
        'lister_les_OF': True,
        'lister_les_formations': True,
        'lister_les_EU': True,
        'lister_les_EI': True,
        'afficher_mon_EU' : True,
        'lister_les_documents': True,
        'lister_les_intervenants': True,
    }

class EI(AbstractUserRole):
    available_permissions = {
        'lister_les_OF': True,
        'lister_les_formations': True,
        'lister_les_EU': True,
        'lister_les_EI': True,
        'afficher_mon_EI' : True,
        'lister_les_documents': True
    }


