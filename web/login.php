<?php
require_once __DIR__ . '/lib/auth.php';
if (current_user()) {
    header('Location: index.php');
    exit;
}
$err = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (login($_POST['username'] ?? '', $_POST['password'] ?? '')) {
        header('Location: index.php');
        exit;
    }
    $err = 'Identifiant ou mot de passe incorrect.';
}
require_once __DIR__ . '/lib/layout.php';
page_header('Connexion', false);
?>
<div class="card">
    <h2>Connexion</h2>
    <?php if ($err) {
        echo '<p class="error">' . htmlspecialchars($err) . '</p>';
    } ?>
    <?php if (users_count() === 0) {
        echo '<p>Aucun compte configuré. <a href="setup.php">Créer le premier compte</a>.</p>';
    } ?>
    <form method="post">
        <label>Identifiant</label>
        <input type="text" name="username" autofocus>
        <label>Mot de passe</label>
        <input type="password" name="password">
        <p><button type="submit">Se connecter</button></p>
    </form>
</div>
<?php page_footer();
