# Déploiement A → Z — Version web (PHP + MySQL) sur dotCanada

Guide complet pour mettre l'application (branche **`web-only`**) en ligne sur
l'hébergement dotCanada, sur un sous-domaine privé. Aucune connaissance serveur
requise : tout passe par le **cPanel** et le **gestionnaire de fichiers**.

> Branche concernée : **`web-only`** du dépôt
> `github.com/romainmmm/appel-mois`.

---

## PHASE 0 — Récupérer le code sur ton PC (Git)

Ouvre **PowerShell** sur le PC où tu prépares le déploiement.

### Première fois (cloner le dépôt et la branche)

```powershell
cd $HOME\Documents
git clone -b web-only https://github.com/romainmmm/appel-mois.git appel-mois-web
cd appel-mois-web
```

### Si le dépôt est déjà cloné (récupérer / mettre à jour la branche)

```powershell
cd $HOME\Documents\appel-mois-web
git fetch origin
git checkout web-only
git pull
```

### Préparer le fichier à téléverser (un ZIP du site)

```powershell
git archive --format=zip --output=site.zip web-only
```

➡️ Cela crée **`site.zip`** contenant exactement ce qu'il faut mettre en ligne
(sans le `config.php` local ni la base de test). C'est ce ZIP qu'on téléverse.

**✅ Test 0 :** le fichier `site.zip` est créé dans le dossier.

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
3. **Téléverser** `site.zip`.
4. Clic droit sur `site.zip` → **Extraire** (« Extract »).
5. Les fichiers (`index.php`, `login.php`, `lib/`, `assets/`…) doivent être
   **directement** dans le dossier du sous-domaine.
6. Supprime `site.zip`.

### Option B — FTP (FileZilla)

Connecte-toi en FTP (identifiants dans cPanel → **Comptes FTP**) et copie tous
les fichiers du dépôt dans le dossier du sous-domaine.

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

## PHASE 5 — Choisir la version de PHP et vérifier les extensions

### 5.1 Trouver l'outil
Dans le cPanel, section **« Logiciels » (Software)**. Selon dotCanada, tu verras
l'un ou les deux outils :
- **MultiPHP Manager** — choisir la version de PHP par domaine.
- **Select PHP Version** (ou « PHP Selector ») — choisir la version **et**
  activer/désactiver les extensions.

### 5.2 Choisir PHP 8.x pour le sous-domaine
1. Ouvrir **MultiPHP Manager**.
2. Dans la liste, **cocher** `menages.motelpanoramique.ca`.
3. Menu **« PHP Version »** (en haut à droite) → choisir **8.1, 8.2 ou 8.3**
   (8.0 minimum).
4. Cliquer **Apply / Appliquer**.

### 5.3 Vérifier / activer les extensions
1. Ouvrir **Select PHP Version** (ou l'onglet **Extensions** du PHP Selector).
2. Vérifier que la version est bien **8.x**.
3. S'assurer que ces cases sont **cochées** :
   - **pdo_mysql** ✅ (obligatoire — connexion à la base)
   - **mysqli** ✅
   - **mbstring** ✅ (accents é, à…)
   - *(pour la répartition plus tard : **zip**, **gd**, **xml**)*
4. Cocher celles qui manquent → **Save / Enregistrer**.

### 5.4 Vérifier que ça marche (test rapide)
Créer un fichier `info.php` dans le dossier du sous-domaine, contenant :

```php
<?php phpinfo();
```

Ouvrir `https://menages.motelpanoramique.ca/info.php`, faire **Ctrl+F** et
chercher **`pdo_mysql`** : tu dois voir une section **PDO** avec
**pdo_mysql → enabled**.
**⚠️ Supprime `info.php` juste après le test** (ne pas le laisser en ligne).

### Si une extension manque ou tu ne trouves pas l'outil
Écris au support dotCanada :
> « Pouvez-vous activer PHP 8.x avec les extensions **pdo_mysql** et
> **mbstring** pour mon sous-domaine menages.motelpanoramique.ca ? »

### Pourquoi c'est important
- **pdo_mysql** : sans elle → erreur « could not find driver » (l'app ne peut
  pas parler à la base).
- **mbstring** : accents corrects.
- **PHP 8** : l'app utilise des fonctions récentes.

**✅ Test 5 :** PHP ≥ 8 et `pdo_mysql` visible comme *enabled*.

---

## PHASE 6 — Créer le premier compte (gérant)

1. Ouvre `https://menages.motelpanoramique.ca/setup.php`
2. Crée le compte **gérant** : identifiant + mot de passe.
3. La page se désactive automatiquement une fois le compte créé.

> Pour ajouter le compte **réception** (et gérer les comptes ensuite) :
> connecte-toi en gérant → onglet **« 👤 Comptes »** → créer le compte
> réception. Cet onglet n'est visible que par le gérant.

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
git checkout web-only
git pull
git archive --format=zip --output=site.zip web-only
```

Puis re-téléverse `site.zip` dans le dossier du sous-domaine et extrais
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
| Récupérer le code | `git clone -b web-only …` puis `git archive … web-only` |

---

## Note importante

Cette version web contient : **connexion + comptes**, la **Feuille du
personnel** (heures, pourboires, paie CSV) et les **Notes**. La **répartition
des ménages** (Feuille du mois / du jour) sera ajoutée ensuite ; elle
nécessitera de vérifier que dotCanada autorise les extensions PHP pour lire les
`.xls`/PDF (zip, gd, mbstring).
