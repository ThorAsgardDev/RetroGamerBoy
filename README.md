# IndieGameBoy

1. Télécharger et installer python 3:
https://www.python.org/downloads/

2. Installer le module python "requests" en tapant la commande:
```
pip install requests
```
3. Installer le module python "twitchio" en tapant la commande:
```
pip install twitchio
```

4. Modifier le fichier config.ini pour renseigner les valeurs:
   - ACCESS_TOKEN (S'obtient ici: https://twitchtokengenerator.com/)
   - GDOC_API_KEY (la méthode pour obtenir une clé API est détaillée ici: https://github.com/ThorAsgardDev/xsplit_retrolection_extension)

5. Modifier le fichier config.ini pour renseigner les valeurs <CLIENT_ID> et <CLIENT_SECRET>, Voici la marche à suivre pour obtenir ces valeurs:
   1. Aller à l'adresse suivante: https://console.developers.google.com/apis/credentials
   2. Cliquer sur "Créer des identifiants" -> ID client OAuth
      - Si vous n'avez pas déjà configuré un écran d'autorisation, un bouton "Configurer l'écran d'autorisation" apparait, cliquer dessus, entrer une valeur dans le champ "Nom de l'application" (ex: MyApp) et cliquer sur le bouton "Enregistrer"
   3. Sélectionner "Autre"
   4. Cliquer sur "Créer"
   5. Noter les valeurs Client id et Client Secret et les mettre dans le fichier config.ini
   6. Cliquer à gauche sur "Tableau de bord"
   7. Cliquer sur "+ACTIVER DES APIS ET DES SERVICES"
   8. Chercher "sheets"
   9. Cliquer sur "Google Sheets API"
   10. Si il y a un bouton GERER, ne rien faire, si il y a un bouton "ACTIVER", cliquer dessus

6. Double cliquer sur le fichier "grant_permissions.bat" et suivre les instructions

7. Double cliquer sur le fichier "indiegamerboy.pyw"

Toutes les valeurs seront mises à jour lors d'un clique sur le bouton "Envoyer vers les fichiers textes"
