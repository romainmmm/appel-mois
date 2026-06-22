<?php
ini_set('display_errors', 1);
error_reporting(E_ALL);
echo "1. démarrage<br>";
require __DIR__ . '/lib/auth.php';
echo "2. fichiers lib chargés<br>";
try {
    echo "3. nombre de comptes = " . users_count();
    echo "<br>✅ tout fonctionne";
} catch (Throwable $e) {
    echo "ERREUR : " . $e->getMessage();
}
