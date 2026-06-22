<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/db.php';
require_once __DIR__ . '/lib/rooms.php';

$notes = data_get('notes', []);
$settings = data_get('settings', ['delete_password' => 'motel']);
$flash = '';
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'add_note') {
        $date = $_POST['date'] ?? '';
        $type = in_array($_POST['type'] ?? '', NOTE_TYPES, true) ? $_POST['type'] : 'Autre';
        $room = $_POST['room'] ?? '';
        $room = ($room === '' || $room === '—') ? null : (int) $room;
        $comment = trim($_POST['comment'] ?? '');
        if ($date === '') {
            $err = 'La date est obligatoire.';
        } elseif (in_array($type, NOTE_SHEET_TYPES, true) && !$room) {
            $err = 'Choisissez un numéro de chambre pour Ménage / Serviette / Chien.';
        } else {
            $notes[] = ['date' => $date, 'type' => $type, 'room' => $room, 'comment' => $comment];
            data_set('notes', $notes);
            $flash = 'Note ajoutée.';
        }
    } elseif ($action === 'del_note') {
        $idx = (int) ($_POST['idx'] ?? -1);
        if (isset($notes[$idx])) {
            array_splice($notes, $idx, 1);
            data_set('notes', $notes);
            $flash = 'Note supprimée.';
        }
    }
}

// Tri par date pour l'affichage (en gardant l'index d'origine pour la suppression)
$indexed = [];
foreach ($notes as $i => $n) {
    $indexed[] = $n + ['_idx' => $i];
}
usort($indexed, fn ($a, $b) => [$a['date'], $a['type']] <=> [$b['date'], $b['type']]);

require_once __DIR__ . '/lib/layout.php';
page_header('Notes');
?>
<h1>📝 Notes / tâches manuelles</h1>
<p style="color:#666">« Ménage », « Serviette » et « Chien » concernent une
chambre (et apparaîtront sur la feuille du jour quand elle sera disponible).
« Autre » est une note libre.</p>
<?php if ($flash) {
    echo '<p class="ok">' . htmlspecialchars($flash) . '</p>';
} ?>
<?php if ($err) {
    echo '<p class="error">' . htmlspecialchars($err) . '</p>';
} ?>

<form method="post" style="display:flex; gap:10px; align-items:end; flex-wrap:wrap;">
    <input type="hidden" name="action" value="add_note">
    <div><label>Date</label><input type="date" name="date" required></div>
    <div><label>Type</label>
        <select name="type">
            <?php foreach (NOTE_TYPES as $t) {
                echo '<option>' . $t . '</option>';
            } ?>
        </select>
    </div>
    <div><label>N° de chambre</label>
        <select name="room">
            <option value="—">—</option>
            <?php foreach (ALL_ROOMS as $r) {
                echo '<option>' . $r . '</option>';
            } ?>
        </select>
    </div>
    <div style="flex:1; min-width:200px;"><label>Commentaire</label>
        <input type="text" name="comment" placeholder="détail (facultatif)"></div>
    <div><button type="submit">➕ Ajouter</button></div>
</form>

<h2 style="margin-top:22px;">Notes enregistrées</h2>
<?php if (empty($indexed)) { ?>
    <p>Aucune note pour le moment.</p>
<?php } else { ?>
    <table>
        <tr><th>Date</th><th>Type</th><th>Chambre</th><th>Commentaire</th><th></th></tr>
        <?php foreach ($indexed as $n) { ?>
            <tr>
                <td><?php echo htmlspecialchars($n['date']); ?></td>
                <td><?php echo htmlspecialchars($n['type']); ?></td>
                <td><?php echo $n['room'] ? (int) $n['room'] : '—'; ?></td>
                <td><?php echo htmlspecialchars($n['comment'] ?? ''); ?></td>
                <td>
                    <form method="post" onsubmit="return confirm('Supprimer cette note ?');">
                        <input type="hidden" name="action" value="del_note">
                        <input type="hidden" name="idx" value="<?php echo (int) $n['_idx']; ?>">
                        <button type="submit">🗑</button>
                    </form>
                </td>
            </tr>
        <?php } ?>
    </table>
<?php } ?>
<?php page_footer();
