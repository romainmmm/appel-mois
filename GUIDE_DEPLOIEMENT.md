# Guide de déploiement en ligne — App ménages Motel Panoramique

Ce guide explique, **pas à pas**, comment mettre l'application en ligne sur un
sous-domaine privé et protégé (ex. `menages.motelpanoramique.ca`), avec stockage
SQLite et sauvegardes.

> **Version concernée :** branche `online-deployment` du dépôt
> `github.com/romainmmm/appel-mois`.

---

## 0. Prérequis importants (à vérifier avec dotCanada)

L'application est un service **Python (Streamlit)** qui tourne en permanence.
Elle **ne fonctionne pas** sur un hébergement mutualisé classique (cPanel / PHP
seul). Il faut :

- Un **VPS** (serveur privé virtuel) sous **Linux (Ubuntu 22.04+)**, idéalement
  **hébergé au Canada** (résidence des données — Loi 25).
- Un **accès SSH** au serveur (utilisateur avec `sudo`).
- La possibilité de créer un **sous-domaine** et un enregistrement DNS.

👉 Si tu es sur un hébergement mutualisé, demande à dotCanada de passer sur un
**VPS** (ou un plan « Python / Node application »). Le reste du guide suppose un
VPS Ubuntu.

---

## 1. Créer le sous-domaine (DNS)

Dans le panneau de gestion DNS de `motelpanoramique.ca` :

- Ajouter un enregistrement **A** :
  - **Nom / Hôte** : `menages`
  - **Valeur** : l'adresse IP publique de ton VPS
  - **TTL** : par défaut

Résultat : `menages.motelpanoramique.ca` pointera vers le serveur.

---

## 2. Se connecter au serveur

```bash
ssh ton_utilisateur@IP_DU_VPS
```

Mettre à jour le système :

```bash
sudo apt update && sudo apt upgrade -y
```

---

## 3. Installer les dépendances système

```bash
sudo apt install -y python3 python3-venv python3-pip git nginx
```

---

## 4. Récupérer l'application

```bash
sudo mkdir -p /opt/motel
sudo chown $USER:$USER /opt/motel
cd /opt/motel
git clone -b online-deployment https://github.com/romainmmm/appel-mois.git .
```

Créer un environnement Python isolé et installer les bibliothèques :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Préparer le stockage des données (SQLite)

Choisir un emplacement **persistant** hors du dossier de code :

```bash
sudo mkdir -p /var/lib/motel
sudo chown $USER:$USER /var/lib/motel
```

La base sera le fichier `/var/lib/motel/motel.db` (créé automatiquement).
On indique ce chemin via la variable d'environnement `MOTEL_DB` (voir étape 7).

---

## 6. Créer les comptes (gérant + réception)

Toujours dans le dossier `/opt/motel`, avec l'environnement activé :

```bash
export MOTEL_DB=/var/lib/motel/motel.db
python manage_users.py set gerant gerant       # demande un mot de passe
python manage_users.py set reception reception # demande un mot de passe
python manage_users.py list                    # vérifier
```

> Les mots de passe sont **hachés** (PBKDF2-SHA256) — jamais stockés en clair.
> Pour changer un mot de passe : relancer `set` avec le même identifiant.

---

## 7. Lancer l'app en service permanent (systemd)

Créer le fichier de service :

```bash
sudo nano /etc/systemd/system/motel.service
```

Contenu (adapter `ton_utilisateur`) :

```ini
[Unit]
Description=App menages Motel Panoramique
After=network.target

[Service]
User=ton_utilisateur
WorkingDirectory=/opt/motel
Environment=MOTEL_DB=/var/lib/motel/motel.db
ExecStart=/opt/motel/venv/bin/streamlit run app.py \
  --server.address 127.0.0.1 \
  --server.port 8520 \
  --server.headless true \
  --browser.gatherUsageStats false
Restart=always

[Install]
WantedBy=multi-user.target
```

Activer et démarrer :

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now motel
sudo systemctl status motel        # doit être "active (running)"
```

> L'app écoute sur `127.0.0.1:8520` (uniquement en local — pas exposée
> directement à Internet). C'est nginx qui la publiera en HTTPS.

---

## 8. Publier via nginx (reverse proxy)

```bash
sudo nano /etc/nginx/sites-available/menages
```

Contenu :

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

        # Indispensable pour Streamlit (websocket)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

Activer le site :

```bash
sudo ln -s /etc/nginx/sites-available/menages /etc/nginx/sites-enabled/
sudo nginx -t        # test de configuration
sudo systemctl reload nginx
```

À ce stade, `http://menages.motelpanoramique.ca` doit afficher la page de
connexion.

---

## 9. Activer le HTTPS (chiffrement) — Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d menages.motelpanoramique.ca
```

Suivre les invites (e-mail, accepter la redirection HTTP → HTTPS). Le
renouvellement est automatique. Le site est maintenant en `https://`.

---

## 10. Rendre l'accès privé (non visible de l'extérieur)

L'app est **déjà protégée par la connexion** (identifiant + mot de passe).
Pour renforcer (« invisible » au public), au choix :

### a) Mot de passe au niveau du serveur (double barrière)

```bash
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd motel   # crée un identifiant d'accès
```

Dans le bloc `location /` de nginx, ajouter :

```nginx
        auth_basic "Accès réservé";
        auth_basic_user_file /etc/nginx/.htpasswd;
```

Puis `sudo nginx -t && sudo systemctl reload nginx`.

### b) Restreindre à l'adresse IP de l'hôtel (optionnel)

Dans `location /` :

```nginx
        allow VOTRE_IP_PUBLIQUE_HOTEL;
        deny all;
```

### c) Empêcher l'indexation Google

Déjà géré : aucune page n'est liée publiquement. On peut aussi ajouter dans
nginx :

```nginx
        add_header X-Robots-Tag "noindex, nofollow" always;
```

### Ajouter un lien depuis le site de l'hôtel

Si tu veux un accès rapide, mets simplement un lien
`https://menages.motelpanoramique.ca` dans une page d'administration du site
(non visible des clients).

---

## 11. Sauvegardes automatiques des données

Créer un script de sauvegarde :

```bash
sudo nano /opt/motel/backup.sh
```

```bash
#!/bin/bash
mkdir -p /var/backups/motel
STAMP=$(date +%Y%m%d-%H%M)
sqlite3 /var/lib/motel/motel.db ".backup '/var/backups/motel/motel-$STAMP.db'"
# Garder seulement les 30 dernières sauvegardes
ls -1t /var/backups/motel/motel-*.db | tail -n +31 | xargs -r rm
```

Rendre exécutable et planifier (tous les jours à 2 h) :

```bash
chmod +x /opt/motel/backup.sh
sudo apt install -y sqlite3
crontab -e
# Ajouter la ligne :
0 2 * * * /opt/motel/backup.sh
```

> Idéalement, copier aussi ces sauvegardes vers un **stockage externe**
> (autre serveur, espace objet) pour la sécurité.

---

## 12. Mettre à jour l'application

Quand de nouvelles versions sont poussées sur GitHub :

```bash
cd /opt/motel
git pull
source venv/bin/activate
pip install -r requirements.txt   # si dépendances modifiées
sudo systemctl restart motel
```

---

## 13. Sécurité & conformité (Loi 25 — Québec)

L'app traite des **données personnelles** (personnel, heures, pourboires,
réservations). Bonnes pratiques :

- **Hébergement au Canada** (résidence des données).
- **HTTPS** activé (étape 9) — données chiffrées en transit.
- **Comptes nommés** + mots de passe forts ; un compte par personne.
- **Accès minimal** : seules les personnes nécessaires (gérant, réception).
- **Sauvegardes** chiffrées/sécurisées et conservées de façon limitée.
- **Pare-feu** : n'ouvrir que les ports 80/443 et SSH.

  ```bash
  sudo ufw allow OpenSSH
  sudo ufw allow 'Nginx Full'
  sudo ufw enable
  ```

- Tenir le serveur à jour (`sudo apt update && sudo apt upgrade`).

---

## Aide-mémoire (commandes utiles)

| Action | Commande |
|---|---|
| État du service | `sudo systemctl status motel` |
| Redémarrer l'app | `sudo systemctl restart motel` |
| Voir les logs | `journalctl -u motel -f` |
| Ajouter / changer un compte | `MOTEL_DB=/var/lib/motel/motel.db python manage_users.py set <nom> <role>` |
| Lister les comptes | `MOTEL_DB=/var/lib/motel/motel.db python manage_users.py list` |
| Sauvegarde manuelle | `/opt/motel/backup.sh` |
| Mettre à jour | `cd /opt/motel && git pull && sudo systemctl restart motel` |

---

## Récapitulatif de l'architecture

```
Navigateur (gérant / réception)
        │  HTTPS (port 443)
        ▼
   nginx  ──(auth, TLS)──►  Streamlit (127.0.0.1:8520)
                                   │
                                   ▼
                        SQLite  /var/lib/motel/motel.db
                                   │
                                   ▼
                     Sauvegardes  /var/backups/motel/
```
