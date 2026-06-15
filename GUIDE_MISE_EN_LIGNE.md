# Mise en ligne — Guide complet pas à pas (avec tests)

Ce guide te fait passer de zéro à l'application **en ligne, privée et testée**.
Il se lit dans l'ordre. À chaque étape importante il y a un **✅ Test** : ne
passe à la suite que si le test réussit.

Il y a **3 phases** :

1. **Phase A — Tester en local sur ton PC** (sans serveur, pour tout valider)
2. **Phase B — Déployer sur le serveur** (dotCanada)
3. **Phase C — Tests finaux + remise au gérant**

---

# PHASE A — Tester en local sur ton PC (Windows)

> But : vérifier la version en ligne (connexion + base de données) sur ta
> machine **avant** de toucher au serveur. Ça n'affecte pas ta version bureau
> habituelle (on clone dans un dossier séparé).

### A1. Récupérer la version en ligne dans un dossier séparé

Ouvre **PowerShell** et tape :

```powershell
cd $HOME\Documents
git clone -b online-deployment https://github.com/romainmmm/appel-mois.git appel-mois-online
cd appel-mois-online
```

### A2. Installer les dépendances

```powershell
pip install -r requirements.txt
```

### A3. Créer les deux comptes

```powershell
python manage_users.py set gerant gerant
python manage_users.py set reception reception
```

À chaque fois, tape un mot de passe (il reste invisible à l'écran), puis
confirme. Vérifie :

```powershell
python manage_users.py list
```

**✅ Test A3 :** la liste affiche `gerant [gerant]` et `reception [reception]`.

### A4. Lancer l'application

```powershell
streamlit run app.py
```

Ton navigateur s'ouvre sur `http://localhost:8501`.

**✅ Test A4 :** une **page de connexion** s'affiche (logo + champs identifiant /
mot de passe).

### A5. Tester la connexion et les fonctions

- Connecte-toi avec `gerant` + ton mot de passe.
- **✅ Test A5a :** tu vois les 4 onglets (Feuille du mois, Feuille du jour,
  Notes, Feuille du personnel).
- Dépose une extraction `.xls` → un calendrier se génère, le bouton
  **⬇️ Télécharger** apparaît et le fichier se télécharge.
- Onglet **Feuille du personnel** → saisis des heures + pourboires → le total
  se calcule → bouton de téléchargement de l'Excel de paie.
- **✅ Test A5b :** ferme complètement le navigateur et l'invite PowerShell
  (`Ctrl+C`), relance `streamlit run app.py`, reconnecte-toi : **les données
  sont toujours là** (preuve que la base SQLite fonctionne).
- Clique « Se déconnecter » → tu reviens à la page de connexion.

### A6. (facultatif) Tester le rôle réception

Reconnecte-toi avec `reception`. Tu as accès aux mêmes onglets (les deux rôles
peuvent utiliser l'app ; les suppressions restent protégées par mot de passe).

> Si tout fonctionne en local, tu es prêt pour le serveur. La base de test est
> dans `appel-mois-online\data\motel.db` (tu peux la supprimer, le serveur en
> créera une neuve).

---

# PHASE B — Déployer sur le serveur dotCanada

## B0. Vérifier le type d'hébergement (étape bloquante)

L'app est un service Python qui tourne en continu : **il faut un VPS Linux**
(pas un hébergement mutualisé / cPanel seul).

**À faire :** contacte le support dotCanada et demande :
> « Je veux héberger une application Python (Streamlit) qui tourne en
> permanence, avec accès SSH et root/sudo. Pouvez-vous me fournir un VPS Ubuntu
> 22.04, de préférence hébergé au Canada ? »

Note bien : **l'adresse IP publique** du VPS, **l'identifiant SSH** et le
**mot de passe** (ou la clé) fournis.

**✅ Test B0 :** tu as une IP, un identifiant et un mot de passe SSH.

## B1. Créer le sous-domaine (DNS)

Dans la gestion DNS de `motelpanoramique.ca` (panneau dotCanada) :

- Type : **A**
- Hôte / Nom : `menages`
- Pointe vers : **l'IP du VPS**
- Enregistre.

**✅ Test B1 :** dans PowerShell, `ping menages.motelpanoramique.ca` renvoie
l'IP du VPS (la propagation DNS peut prendre de quelques minutes à 1 h).

## B2. Se connecter au serveur (depuis Windows)

Dans PowerShell :

```powershell
ssh ton_identifiant@IP_DU_VPS
```

Tape `yes` à la première connexion, puis le mot de passe.

**✅ Test B2 :** l'invite devient celle du serveur (ex. `ubuntu@vps:~$`).

> À partir d'ici, **toutes les commandes se tapent dans cette session SSH**
> (sur le serveur), pas sur ton PC.

## B3. Mettre à jour et installer les outils

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git nginx sqlite3
```

## B4. Installer l'application

```bash
sudo mkdir -p /opt/motel && sudo chown $USER:$USER /opt/motel
cd /opt/motel
git clone -b online-deployment https://github.com/romainmmm/appel-mois.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## B5. Préparer la base de données + les comptes

```bash
sudo mkdir -p /var/lib/motel && sudo chown $USER:$USER /var/lib/motel
export MOTEL_DB=/var/lib/motel/motel.db
python manage_users.py set gerant gerant
python manage_users.py set reception reception
python manage_users.py list
```

**✅ Test B5 :** la liste affiche les deux comptes.

## B6. Lancer l'app comme service permanent

```bash
sudo nano /etc/systemd/system/motel.service
```

Colle ceci (remplace `ton_identifiant` par ton utilisateur du serveur) :

```ini
[Unit]
Description=App menages Motel Panoramique
After=network.target

[Service]
User=ton_identifiant
WorkingDirectory=/opt/motel
Environment=MOTEL_DB=/var/lib/motel/motel.db
ExecStart=/opt/motel/venv/bin/streamlit run app.py --server.address 127.0.0.1 --server.port 8520 --server.headless true --browser.gatherUsageStats false
Restart=always

[Install]
WantedBy=multi-user.target
```

Enregistre (`Ctrl+O`, `Entrée`, `Ctrl+X`), puis :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now motel
sudo systemctl status motel
```

**✅ Test B6 :** le statut affiche **active (running)** (appuie sur `q` pour
sortir). Sinon : `journalctl -u motel -e` pour voir l'erreur.

## B7. Publier le site (nginx)

```bash
sudo nano /etc/nginx/sites-available/menages
```

Colle :

```nginx
server {
    listen 80;
    server_name menages.motelpanoramique.ca;

    location / {
        proxy_pass http://127.0.0.1:8520;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Active :

```bash
sudo ln -s /etc/nginx/sites-available/menages /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

**✅ Test B7 :** depuis ton PC, ouvre `http://menages.motelpanoramique.ca` →
la page de connexion s'affiche.

## B8. Activer le HTTPS (cadenas, chiffrement)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d menages.motelpanoramique.ca
```

Donne un e-mail, accepte, et choisis la **redirection HTTP → HTTPS**.

**✅ Test B8 :** `https://menages.motelpanoramique.ca` s'ouvre avec un
**cadenas** dans le navigateur.

## B9. Sécuriser le pare-feu

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## B10. Rendre l'accès privé (recommandé)

Deuxième barrière par mot de passe au niveau du serveur :

```bash
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd motel
sudo nano /etc/nginx/sites-available/menages
```

Dans le bloc `location /`, ajoute ces 3 lignes :

```nginx
        auth_basic "Accès réservé";
        auth_basic_user_file /etc/nginx/.htpasswd;
        add_header X-Robots-Tag "noindex, nofollow" always;
```

Puis :

```bash
sudo nginx -t && sudo systemctl reload nginx
```

**✅ Test B10 :** à l'ouverture du site, le navigateur demande d'abord un
identifiant (barrière serveur), **puis** la page de connexion de l'app.

## B11. Sauvegardes automatiques

```bash
nano /opt/motel/backup.sh
```

```bash
#!/bin/bash
mkdir -p /var/backups/motel
STAMP=$(date +%Y%m%d-%H%M)
sqlite3 /var/lib/motel/motel.db ".backup '/var/backups/motel/motel-$STAMP.db'"
ls -1t /var/backups/motel/motel-*.db | tail -n +31 | xargs -r rm
```

```bash
chmod +x /opt/motel/backup.sh
crontab -e
```

Ajoute en bas (sauvegarde quotidienne à 2 h) :

```
0 2 * * * /opt/motel/backup.sh
```

**✅ Test B11 :** lance `/opt/motel/backup.sh` puis
`ls /var/backups/motel/` → un fichier `motel-….db` est présent.

---

# PHASE C — Tests d'acceptation (dans l'app en ligne)

Connecte-toi sur `https://menages.motelpanoramique.ca` et coche :

- [ ] Connexion `gerant` réussie ; mauvais mot de passe refusé.
- [ ] **Feuille du mois** : dépôt d'un `.xls` → calendrier + téléchargement Excel **et** PDF.
- [ ] **Feuille du jour** : choix d'une date → feuille du jour Excel/PDF.
- [ ] **Notes** : ajout Ménage/Serviette/Chien → apparaît sur la feuille du jour ; « Autre » non.
- [ ] **Feuille du personnel** : saisie heures + pourboires → totaux corrects.
- [ ] **Excel de paie** : téléchargement → totaux par employé corrects.
- [ ] **Employé hors équipe** : ajout (ex. réception) → compte ses heures, **absent** de la répartition.
- [ ] **Suppression** d'un membre → demande le mot de passe (`motel` par défaut).
- [ ] **Persistance** : se déconnecter / fermer / rouvrir → les données sont conservées.
- [ ] **Déconnexion** fonctionne.

Si tout est coché : **l'application est en ligne et opérationnelle.** 🎉

---

# Remise au gérant

Donne au gérant et à la réception :

- L'adresse : `https://menages.motelpanoramique.ca`
- L'identifiant de la barrière serveur (étape B10), si activée
- Leur identifiant + mot de passe de l'app
- Rappel : pour changer le **mot de passe de suppression**, onglet Feuille du
  mois → « Gérer l'équipe » → section 🔒.

---

# Dépannage rapide

| Problème | Quoi faire (sur le serveur, en SSH) |
|---|---|
| Le site ne s'ouvre pas | `sudo systemctl status motel` puis `journalctl -u motel -e` |
| Erreur 502 (Bad Gateway) | Le service est arrêté → `sudo systemctl restart motel` |
| Page blanche / connexion qui boucle | Vérifier les lignes `Upgrade`/`Connection` dans nginx (étape B7) |
| « Aucun compte configuré » | Refaire l'étape B5 (`manage_users.py set …`) |
| Changer un mot de passe | `MOTEL_DB=/var/lib/motel/motel.db python manage_users.py set <nom> <role>` |
| Mettre à jour l'app | `cd /opt/motel && git pull && sudo systemctl restart motel` |

> Astuce : pour réexécuter `manage_users.py`, va d'abord dans le dossier et
> active l'environnement : `cd /opt/motel && source venv/bin/activate`.
