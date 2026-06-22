# Déploiement A → Z — Version web (PHP + MySQL) sur dotCanada

Guide complet pour mettre l'application (branche **`web-app`**) en ligne sur
l'hébergement dotCanada, sur un sous-domaine privé. Aucune connaissance serveur
requise : tout passe par le **cPanel** et le **gestionnaire de fichiers**.

> Branche concernée : **`web-app`** du dépôt
> `github.com/romainmmm/appel-mois`.

---

## PHASE 0 — Récupérer le code sur ton PC (Git)

Ouvre **PowerShell** sur le PC où tu prépares le déploiement.

### Première fois (cloner le dépôt et la branche)

```powershell
cd $HOME\Documents
git clone -b web-app https://github.com/romainmmm/appel-mois.git appel-mois-web
cd appel-mois-web
```

### Si le dépôt est déjà cloné (récupérer / mettre à jour la branche)

```powershell
cd $HOME\Documents\appel-mois-web
git fetch origin
git checkout web-app
git pull
```

### Préparer le fichier à téléverser (un ZIP du dossier `web/`)

```powershell
git archive --format=zip --output=web.zip web-app:web
```

➡️ Cela crée **`web.zip`** contenant exactement ce qu'il faut mettre en ligne
(sans le `config.php` local ni la base de test). C'est ce ZIP qu'on téléverse.

**✅ Test 0 :** le fichier `web.zip` est créé dans le dossier.

---

## PHASE 1 — Créer le sous-domaine (cPanel)

1. Connecte-toi au **cPanel** de dotCanada.
2. Section **Domaines** → **Sous-domaines** (« Subdomains »).
3. Crée `menages` → ça donne `menages.motelpanoramique.ca`.
4. Note le **dossier racine** indiqué (ex. `public_html/menages` ou
   `/home/COMPTE/menages`).

**✅ Test 1 :** ouvrir `http://menages.motelpanoramique.ca` affiche une page
vide ou « Index of » (le dossier existe).

---

## PHASE 2 — Créer la base de données MySQL (cPanel)

1. cPanel → **Bases de données MySQL** (« MySQL Databases »).
2. **Créer une base** : nom ex. `menages` (le cPanel ajoute un préfixe →
   ça donne par ex. `motel_menages`). **Note le nom complet.**
3. **Créer un utilisateur** MySQL + mot de passe. **Note-les.**
4. Section **« Ajouter un utilisateur à une base »** : associe l'utilisateur à
   la base, coche **TOUS LES PRIVILÈGES**.

**✅ Test 2 :** tu as noté : **nom de base**, **utilisateur**, **mot de passe**.
(L'hôte est presque toujours `localhost`.)

---

## PHASE 3 — Téléverser les fichiers

### Option A — Gestionnaire de fichiers cPanel (le plus simple)

1. cPanel → **Gestionnaire de fichiers**.
2. Va dans le **dossier racine du sous-domaine** (Phase 1).
3. **Téléverser** `web.zip`.
4. Clic droit sur `web.zip` → **Extraire** (« Extract »).
5. Les fichiers (`index.php`, `login.php`, `lib/`, `assets/`…) doivent être
   **directement** dans le dossier du sous-domaine (pas dans un sous-dossier
   `web/`). Si l'extraction a créé un dossier `web/`, déplace son contenu d'un
   niveau vers le haut.
6. Supprime `web.zip`.

### Option B — FTP (FileZilla)

Connecte-toi en FTP (identifiants dans cPanel → **Comptes FTP**) et copie le
contenu du dossier `web/` dans le dossier du sous-domaine.

**✅ Test 3 :** dans le gestionnaire de fichiers, tu vois `index.php`,
`login.php`, `setup.php`, le dossier `lib/` et `assets/` dans le dossier du
sous-domaine.

---

## PHASE 4 — Configurer la connexion à la base

1. Dans le gestionnaire de fichiers, **copie** `config.example.php` en
   **`config.php`** (clic droit → Copier, puis renommer).
2. **Édite `config.php`** (clic droit → Modifier) et mets tes infos de la
   Phase 2 :

```php
<?php
define('DB_DRIVER', 'mysql');
define('DB_HOST', 'localhost');
define('DB_NAME', 'motel_menages');   // ton nom de base complet
define('DB_USER', 'motel_user');      // ton utilisateur
define('DB_PASS', 'TON_MOT_DE_PASSE');// ton mot de passe
define('DB_SQLITE', __DIR__ . '/data/app.db');
define('APP_TITLE', 'Gestion des ménages — Motel Panoramique');
```

3. Enregistre.

---

## PHASE 5 — Vérifier la version de PHP

1. cPanel → **Sélectionner la version de PHP** (« Select PHP Version » /
   « MultiPHP Manager »).
2. Choisis **PHP 8.0 ou plus** pour le sous-domaine.
3. Vérifie que **`pdo_mysql`** et **`mbstring`** sont **cochées** (activées).
   (Elles le sont presque toujours par défaut.)

**✅ Test 5 :** PHP ≥ 8 et `pdo_mysql` activé.

---

## PHASE 6 — Créer le premier compte (gérant)

1. Ouvre `https://menages.motelpanoramique.ca/setup.php`
2. Crée le compte **gérant** : identifiant + mot de passe.
3. La page se désactive automatiquement une fois le compte créé.

> Pour ajouter le compte **réception** : pour l'instant, tu peux créer un
> 2ᵉ compte via phpMyAdmin (m'écrire et je te donne la marche à suivre), ou
> j'ajoute bientôt une page d'administration des comptes.

**✅ Test 6 :** `setup.php` affiche « Compte gérant créé ».

---

## PHASE 7 — Sécurité (HTTPS + privé)

1. **HTTPS** : cPanel → **SSL/TLS** ou **AutoSSL** → activer le certificat pour
   `menages.motelpanoramique.ca`. Active la **redirection HTTPS** si proposée.
2. **(Optionnel) Double barrière** : cPanel → **Confidentialité du répertoire**
   (« Directory Privacy ») → protéger le dossier du sous-domaine par un mot de
   passe supplémentaire.

**✅ Test 7 :** `https://menages.motelpanoramique.ca` s'ouvre avec le **cadenas**.

---

## PHASE 8 — Tests d'acceptation

Connecte-toi sur `https://menages.motelpanoramique.ca/` et vérifie :

- [ ] Connexion `gerant` réussie ; mauvais mot de passe refusé.
- [ ] Onglet **Feuille du personnel** : ajouter un employé (ex. réception).
- [ ] Saisir des heures + pourboires → le **total** est correct.
- [ ] Télécharger la **paie (CSV)** → s'ouvre dans Excel, totaux corrects.
- [ ] Supprimer un employé → demande le **mot de passe** (`motel` par défaut).
- [ ] Depuis un **autre PC** du même accès → **mêmes données** (base partagée).
- [ ] **Se déconnecter** fonctionne.

🎉 Si tout est coché : l'application web est en ligne et partagée.

---

## PHASE 9 — Mettre à jour plus tard

Quand de nouvelles versions sont publiées :

```powershell
cd $HOME\Documents\appel-mois-web
git checkout web-app
git pull
git archive --format=zip --output=web.zip web-app:web
```

Puis re-téléverse `web.zip` dans le dossier du sous-domaine et extrais
(**sans écraser `config.php`**). Les données dans MySQL ne sont pas touchées.

---

## Sauvegardes

- cPanel propose des **sauvegardes** du compte.
- Pour la base seule : cPanel → **phpMyAdmin** → choisir la base → **Exporter**
  → enregistre un fichier `.sql` (à faire régulièrement, ex. chaque mois).

---

## Aide-mémoire

| Besoin | Où |
|---|---|
| Voir / sauvegarder les données | cPanel → **phpMyAdmin** |
| Changer les identifiants de base | `config.php` |
| Ajouter un sous-domaine | cPanel → Sous-domaines |
| Activer HTTPS | cPanel → SSL/TLS (AutoSSL) |
| Récupérer le code | `git clone -b web-app …` puis `git archive … web-app:web` |

---

## Note importante

Cette version web contient pour l'instant la **Feuille du personnel** (heures,
pourboires, paie) — la fonction qui profite le plus du partage entre postes.
Les **Notes** et la **répartition des ménages** (Feuille du mois / du jour)
seront ajoutées ensuite ; la répartition nécessitera de vérifier que dotCanada
autorise les extensions PHP pour lire les `.xls`/PDF (zip, gd, mbstring).
