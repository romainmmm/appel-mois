# Déploiement de la version web (PHP + MySQL) sur dotCanada

Cette version tourne sur l'**hébergement mutualisé** existant (PHP + MySQL),
sur un **sous-domaine**. Aucune installation de serveur, le site et l'app sont
chez le même hébergeur.

> Statut : **socle prêt** (connexion + base de données). Les fonctions
> (répartition, feuille du jour, notes, personnel) sont ajoutées par phases.

---

## Étape 1 — Créer le sous-domaine (cPanel)

1. cPanel → **Domaines** → **Sous-domaines** (ou « Domains »).
2. Créer `menages` → `menages.motelpanoramique.ca`.
3. Noter le **dossier racine** créé (ex. `/home/compte/menages`).

## Étape 2 — Créer la base de données MySQL (cPanel)

1. cPanel → **Bases de données MySQL**.
2. Créer une base : ex. `motel_menages`.
3. Créer un utilisateur MySQL + mot de passe.
4. **Ajouter l'utilisateur à la base** avec **tous les privilèges**.
5. Noter : nom de base, utilisateur, mot de passe, hôte (souvent `localhost`).

## Étape 3 — Téléverser les fichiers

1. Récupérer le contenu du dossier **`web/`** du dépôt (branche `web-only`).
   - Via **Gestionnaire de fichiers** cPanel (téléverser un ZIP puis extraire),
     ou via **FTP**.
2. Mettre tous les fichiers dans le **dossier racine du sous-domaine**.

## Étape 4 — Configurer la connexion à la base

1. Copier `config.example.php` en **`config.php`**.
2. Y mettre les infos MySQL de l'étape 2 :
   ```php
   define('DB_DRIVER', 'mysql');
   define('DB_HOST', 'localhost');
   define('DB_NAME', 'motel_menages');
   define('DB_USER', 'motel_user');
   define('DB_PASS', 'le_mot_de_passe');
   ```

## Étape 5 — Vérifier la version de PHP

cPanel → **Sélectionner la version de PHP** (« MultiPHP » / « Select PHP
Version ») → choisir **PHP 8.0 ou plus**, et vérifier que les extensions
**pdo_mysql** et **mbstring** sont activées (elles le sont généralement).

## Étape 6 — Créer le premier compte

1. Ouvrir `https://menages.motelpanoramique.ca/setup.php`.
2. Créer le compte **gérant** (identifiant + mot de passe).
3. Une fois fait, la page `setup.php` se désactive automatiquement.

**✅ Test :** ouvrir `https://menages.motelpanoramique.ca/` → page de connexion
→ se connecter → le tableau de bord s'affiche.

## Étape 7 — Sécuriser (recommandé)

- **HTTPS** : activer le certificat SSL gratuit dans cPanel (**SSL/TLS** ou
  **AutoSSL**) pour le sous-domaine.
- Forcer HTTPS : cPanel propose souvent une case « Force HTTPS Redirect ».
- (Optionnel) Protéger le dossier par mot de passe : cPanel → **Confidentialité
  du répertoire**.

---

## Mises à jour

Re-téléverser les fichiers modifiés (sans écraser
`config.php` ni le dossier `data/`).

## Notes

- **Données partagées** : tous les postes lisent/écrivent la même base MySQL →
  données identiques partout, accessibles de n'importe où.
- **Sauvegardes** : utiliser les sauvegardes cPanel, ou exporter la base via
  **phpMyAdmin** régulièrement.
