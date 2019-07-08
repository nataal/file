# Déploiement de l'application mase

## Langage de développement : Python3

## Framework : Django

## Fichiers de dépendances : requirements.txt

## Fichiers de configuration :

- Production: config/settings/prod.py

- Développement: config/settings/local.py

## Module wsgi: config/wsgi.py

## Variables d'environnement à créer :

### Amazon Web Services Keys
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_STORAGE_BUCKET_NAME
- AWS_SES_ACCESS_KEY_ID
- AWS_SES_SECRET_KEY


### DJANGO CONFIGURATION KEYS
- SECRET_KEY
- database_name
- database_password
- DJANGO_SETTINGS_MODULE


## Serveur de fichiers statiques : Les fichiers sont stockés sur AWS S3. La configuration est faite dans le fichier config/settings/prod.py

## Serveur SMTP : La configuration du serveur d'envoi de mail est dans le dossier config/settings/base.py .

## Etapes de déploiement :

- Définir les variables d'environnement
- Installer les dépendances : pip3 install -r requirements.txt
- Initialiser la base de données : python3 manage.py migrate
- Lancer le serveur
