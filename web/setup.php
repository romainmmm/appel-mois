<?php
require_once __DIR__ . '/lib/auth.php';
require_once __DIR__ . '/lib/layout.php';

// Once accounts exist, this page is disabled (further accounts are managed
// from the admin area by a gérant — phase 2).
if (users_count() > 0) {
    page_header('Configuration', false);
    echo '<div class="card"><p>Des comptes existent déjà.</p>'
        . '<p><a href="login.php">Aller à la connexion</a></p></div>';
    page_footer();
    exit;
}

$err = '';
$done = false;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $u = trim($_POST['username'] ?? '');
    $p = $_POST['password'] ?? '';
    if ($u === '' || $p === '') {
        $err = 'Veuillez remplir tous les champs.';
    } else {
        create_user($u, $p, 'gerant');
        $done = true;
    }
}

page_header('Configuration initiale', false);
if ($done) {
    echo '<div class="card"><p class="ok">Compte gérant créé.</p>'
        . '<p><a href="login.php">Aller à la connexion</a></p></div>';
} else {
    ?>
    <div class="card">
        <h2>Créer le compte gérant</h2>
        <?php if ($err) {
            echo '<p class="error">' . htmlspecialchars($err) . '</p>';
        } ?>
        <form method="post">
            <label>Identifiant</label>
            <input type="text" name="username" value="gerant">
            <label>Mot de passe</label>
            <input type="password" name="password">
            <p><button type="submit">Créer le compte</button></p>
        </form>
    </div>
    <?php
}
page_footer();
