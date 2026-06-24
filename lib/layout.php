<?php
require_once __DIR__ . '/auth.php';

function page_header(string $title = '', bool $with_nav = true): void
{
    $u = current_user();
    $appTitle = defined('APP_TITLE') ? APP_TITLE : 'Motel Panoramique';
    echo '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">';
    echo '<meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<meta name="robots" content="noindex, nofollow">';
    echo '<title>' . htmlspecialchars($title ?: $appTitle) . '</title>';
    echo '<link rel="stylesheet" href="assets/style.css"></head><body>';

    echo '<header class="brand">';
    if (file_exists(__DIR__ . '/../assets/logo_motel.png')) {
        echo '<img src="assets/logo_motel.png" alt="logo">';
    }
    echo '<div class="titles"><div class="t1">MOTEL PANORAMIQUE</div>';
    echo '<div class="t2">Gestion des ménages · Saguenay, Qc</div></div>';
    if ($u) {
        echo '<div class="userbox">' . htmlspecialchars($u['username'])
            . ' <span class="role">(' . htmlspecialchars($u['role']) . ')</span>'
            . ' &nbsp;<a class="logout" href="logout.php">Se déconnecter</a></div>';
    }
    echo '</header>';

    if ($with_nav && $u) {
        echo '<nav class="tabs">';
        $tabs = [
            'index.php'     => '📅 Feuille du mois',
            'jour.php'      => '📋 Feuille du jour',
            'notes.php'     => '📝 Notes',
            'personnel.php' => '🗓️ Personnel',
        ];
        if (is_gerant()) {
            $tabs['equipe.php'] = '⚙️ Équipe';
            $tabs['admin.php'] = '👤 Comptes';
        }
        $cur = basename($_SERVER['PHP_SELF']);
        foreach ($tabs as $href => $label) {
            $active = ($href === $cur) ? ' class="active"' : '';
            echo '<a' . $active . ' href="' . $href . '">' . $label . '</a>';
        }
        echo '</nav>';
    }
    echo '<main class="container">';
}

function page_footer(): void
{
    echo '</main></body></html>';
}
