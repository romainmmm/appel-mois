<?php
/**
 * Copier ce fichier en "config.php" et adapter les valeurs.
 *
 * Sur dotCanada (production) : utiliser MySQL (créé dans cPanel).
 * En local (test)            : utiliser SQLite (aucune installation).
 */

// 'mysql' (dotCanada) ou 'sqlite' (test local)
define('DB_DRIVER', 'mysql');

// --- MySQL (dotCanada) ---
define('DB_HOST', 'localhost');
define('DB_NAME', 'motel_menages');        // nom de la base créée dans cPanel
define('DB_USER', 'motel_user');           // utilisateur MySQL
define('DB_PASS', 'CHANGER_MOI');          // mot de passe MySQL

// --- SQLite (test local) ---
define('DB_SQLITE', __DIR__ . '/data/app.db');

define('APP_TITLE', 'Gestion des ménages — Motel Panoramique');
