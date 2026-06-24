<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/staff_config.php';

if (!is_gerant()) {
    require_once __DIR__ . '/lib/layout.php';
    page_header('Équipe');
    echo '<p class="error">Cette page est réservée au gérant.</p>';
    page_footer();
    exit;
}

$team = load_team();
$flash = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    if ($action === 'save') {
        $new = [];
        foreach ($_POST['name'] ?? [] as $i => $name) {
            $name = trim($name);
            if ($name === '') continue;
            $wm = [];
            for ($d = 0; $d < 7; $d++) {
                $v = (int)($_POST['cap'][$i][$d] ?? 0);
                if ($v > 0) $wm[$d] = $v;
            }
            $off = array_filter(array_map('trim', explode(',', $_POST['off'][$i] ?? '')));
            $floor = $_POST['floor'][$i] ?? '';
            $new[] = [
                'name' => $name,
                'order' => (int)($_POST['order'][$i] ?? ($i + 1)),
                'home_floor' => ($floor === '' ? null : (int)$floor),
                'floor_strict' => !empty($_POST['strict'][$i]),
                'weekly_max' => $wm,
                'days_off' => array_values($off),
            ];
        }
        usort($new, fn($a, $b) => $a['order'] <=> $b['order']);
        save_team($new);
        $team = $new;
        $flash = 'Équipe enregistrée.';
    } elseif ($action === 'add') {
        $team[] = ['name' => 'Nouvelle', 'order' => count($team) + 1, 'home_floor' => null,
                   'floor_strict' => false, 'weekly_max' => [0=>6,1=>6,2=>6,3=>6,4=>6,5=>6,6=>6], 'days_off' => []];
        save_team($team);
        $flash = 'Préposée ajoutée.';
    }
}

require_once __DIR__ . '/lib/layout.php';
page_header('Équipe');
?>
<h1>⚙️ Gérer l'équipe ménage</h1>
<p style="color:#666">Ordre = priorité de répartition. Étage = étage attitré
(laisser vide = flexible). « Strict » = ne fait que son étage. Plafond = nombre
max de chambres par jour (0 = ne travaille pas ce jour). Congés = dates AAAA-MM-JJ
séparées par des virgules.</p>
<?php if ($flash) echo '<p class="ok">' . htmlspecialchars($flash) . '</p>'; ?>

<form method="post">
    <input type="hidden" name="action" value="save">
    <table>
        <tr>
            <th>Nom</th><th>Ordre</th><th>Étage</th><th>Strict</th>
            <?php foreach (WEEKDAYS_FR_SHORT as $d) echo '<th>' . $d . '</th>'; ?>
            <th>Congés (AAAA-MM-JJ)</th>
        </tr>
        <?php foreach (array_values($team) as $i => $w) { ?>
            <tr>
                <td><input type="text" name="name[<?php echo $i; ?>]" value="<?php echo htmlspecialchars($w['name']); ?>" style="width:110px"></td>
                <td><input type="number" name="order[<?php echo $i; ?>]" value="<?php echo (int)$w['order']; ?>" style="width:50px"></td>
                <td>
                    <select name="floor[<?php echo $i; ?>]" style="width:90px">
                        <?php foreach (['' => 'Flexible', '100' => '100', '200' => '200', '300' => '300', '400' => '400'] as $v => $lbl) {
                            $sel = ((string)$w['home_floor'] === (string)$v) ? 'selected' : '';
                            echo "<option value=\"$v\" $sel>$lbl</option>";
                        } ?>
                    </select>
                </td>
                <td style="text-align:center"><input type="checkbox" name="strict[<?php echo $i; ?>]" <?php echo $w['floor_strict'] ? 'checked' : ''; ?>></td>
                <?php for ($d = 0; $d < 7; $d++) { ?>
                    <td><input type="number" min="0" max="30" name="cap[<?php echo $i; ?>][<?php echo $d; ?>]"
                        value="<?php echo (int)($w['weekly_max'][$d] ?? 0); ?>" style="width:46px"></td>
                <?php } ?>
                <td><input type="text" name="off[<?php echo $i; ?>]" value="<?php echo htmlspecialchars(implode(',', $w['days_off'])); ?>" style="width:160px"></td>
            </tr>
        <?php } ?>
    </table>
    <p><button type="submit">💾 Enregistrer l'équipe</button></p>
</form>

<form method="post"><input type="hidden" name="action" value="add">
    <button type="submit">➕ Ajouter une préposée</button>
</form>
<p style="color:#666">Pour supprimer une préposée : videz son nom puis enregistrez.</p>
<?php page_footer();
