<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
if (!file_exists(__DIR__.'/config.php')) { exit('config.php INTROUVABLE (mauvais nom / extension .txt ?)'); }
require __DIR__.'/config.php';
echo 'DRIVER = ' . DB_DRIVER . '<br>';
try {
    if (DB_DRIVER === 'mysql') {
        $pdo = new PDO('mysql:host='.DB_HOST.';dbname='.DB_NAME.';charset=utf8mb4', DB_USER, DB_PASS);
        echo 'Connexion MySQL OK ✅';
    } else {
        echo 'DB_DRIVER nest pas mysql !';
    }
} catch (Throwable $e) {
    echo 'ERREUR : ' . $e->getMessage();
}
