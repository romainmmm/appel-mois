<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/db.php';

$me = current_user();
$settings = data_get('settings', ['delete_password' => 'motel']);
$flash = '';
$err = '';

// Réservé au gérant
if (!is_gerant()) {
    require_once __DIR__ . '/lib/layout.php';
    page_header('Comptes');
    echo '<p class="error">Cette page est réservée au gérant.</p>';
    page_footer();
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'add_user') {
        $u = trim($_POST['username'] ?? '');
        $p = $_POST['password'] ?? '';
        $role = ($_POST['role'] ?? 'reception') === 'gerant' ? 'gerant' : 'reception';
        if ($u === '' || $p === '') {
            $err = 'Identifiant et mot de passe obligatoires.';
        } elseif (find_user($u)) {
            $err = "L'identifiant « $u » existe déjà.";
        } else {
            create_user($u, $p, $role);
            $flash = "Compte « $u » créé ($role).";
        }
    } elseif ($action === 'set_pw') {
        $u = $_POST['username'] ?? '';
        $p = $_POST['password'] ?? '';
        if ($p === '') {
            $err = 'Le nouveau mot de passe ne peut pas être vide.';
        } elseif (find_user($u)) {
            set_password($u, $p);
            $flash = "Mot de passe de « $u » modifié.";
        }
    } elseif ($action === 'del_user') {
        $u = $_POST['username'] ?? '';
        $pw = $_POST['pw'] ?? '';
        if ($pw !== ($settings['delete_password'] ?? 'motel')) {
            $err = 'Mot de passe de suppression incorrect.';
        } elseif ($u === $me['username']) {
            $err = 'Vous ne pouvez pas supprimer votre propre compte.';
        } else {
            $target = find_user($u);
            if ($target && $target['role'] === 'gerant' && count_gerants() <= 1) {
                $err = 'Impossible de supprimer le dernier compte gérant.';
            } elseif ($target) {
                delete_user($u);
                $flash = "Compte « $u » supprimé.";
            }
        }
    }
}

require_once __DIR__ . '/lib/layout.php';
page_header('Comptes');
?>
<h1>👤 Gestion des comptes</h1>
<?php if ($flash) {
    echo '<p class="ok">' . htmlspecialchars($flash) . '</p>';
} ?>
<?php if ($err) {
    echo '<p class="error">' . htmlspecialchars($err) . '</p>';
} ?>

<h2>Ajouter un compte</h2>
<form method="post" style="display:flex; gap:10px; align-items:end; flex-wrap:wrap;">
    <input type="hidden" name="action" value="add_user">
    <div><label>Identifiant</label><input type="text" name="username" required></div>
    <div><label>Mot de passe</label><input type="password" name="password" required></div>
    <div><label>Rôle</label>
        <select name="role">
            <option value="reception">Réception</option>
            <option value="gerant">Gérant</option>
        </select>
    </div>
    <div><button type="submit">➕ Créer</button></div>
</form>

<h2 style="margin-top:24px;">Comptes existants</h2>
<table style="max-width:760px;">
    <tr><th>Identifiant</th><th>Rôle</th><th>Réinitialiser le mot de passe</th><th>Supprimer</th></tr>
    <?php foreach (all_users() as $row) {
        $u = $row['username'];
        ?>
        <tr>
            <td><?php echo htmlspecialchars($u); ?>
                <?php echo $u === $me['username'] ? ' <em>(vous)</em>' : ''; ?></td>
            <td><?php echo htmlspecialchars($row['role']); ?></td>
            <td>
                <form method="post" style="display:flex; gap:6px;">
                    <input type="hidden" name="action" value="set_pw">
                    <input type="hidden" name="username" value="<?php echo htmlspecialchars($u); ?>">
                    <input type="password" name="password" placeholder="nouveau" style="width:140px">
                    <button type="submit">Changer</button>
                </form>
            </td>
            <td>
                <form method="post" style="display:flex; gap:6px;"
                      onsubmit="return confirm('Supprimer le compte <?php echo htmlspecialchars($u); ?> ?');">
                    <input type="hidden" name="action" value="del_user">
                    <input type="hidden" name="username" value="<?php echo htmlspecialchars($u); ?>">
                    <input type="password" name="pw" placeholder="mot de passe" style="width:130px">
                    <button type="submit">🗑</button>
                </form>
            </td>
        </tr>
    <?php } ?>
</table>
<p style="color:#666; margin-top:10px;">Le « mot de passe de suppression »
(par défaut <code>motel</code>) protège les suppressions.</p>
<?php page_footer();
