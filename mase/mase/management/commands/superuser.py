from django.core.management import BaseCommand

from mase.mase.models import Utilisateur

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not Utilisateur.objects.filter(email="madiallob@gmail.com"):
            u = Utilisateur.objects.create_superuser(email="madiallob@gmail.com", password="MaseSiteAdmin2018")
            u.is_active = True
            u.save()
            self.stdout.write(self.style.SUCCESS('Superadmin cree'))
        else:
            self.stdout.write(self.style.SUCCESS('Superadmin deja existant'))