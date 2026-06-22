<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/timesheet.php';

// ── Load data ───────────────────────────────────────────────────────
$employees = data_get('employees', null);
if ($employees === null) {
    // Seed the cleaning team on first use; reception etc. can be added.
    $employees = array_map(
        fn ($n) => ['name' => $n, 'role' => 'Équipe ménage'],
        ['Anna', 'Isabelle', 'Oumar', 'Morgann', 'Estrella', 'Fatoumata', 'Chantale']
    );
    data_set('employees', $employees);
}
$settings = data_get('settings', ['delete_password' => 'motel']);
$timesheet = data_get('timesheet', []);

$flash = '';
$err = '';

// ── Handle actions ──────────────────────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'add_emp') {
        $name = trim($_POST['name'] ?? '');
        $role = trim($_POST['role'] ?? '');
        if ($name !== '' && !in_array($name, array_column($employees, 'name'), true)) {
            $employees[] = ['name' => $name, 'role' => $role];
            data_set('employees', $employees);
            $flash = "Employé « $name » ajouté.";
        }
    } elseif ($action === 'del_emp') {
        $name = $_POST['name'] ?? '';
        $pw = $_POST['pw'] ?? '';
        if ($pw !== ($settings['delete_password'] ?? 'motel')) {
            $err = 'Mot de passe incorrect — suppression annulée.';
        } else {
            $employees = array_values(array_filter($employees, fn ($e) => $e['name'] !== $name));
            data_set('employees', $employees);
            $flash = "Employé « $name » supprimé.";
        }
    } elseif ($action === 'save_sheet') {
        $emp = $_POST['emp'] ?? '';
        $start = $_POST['start'] ?? '';
        $dates = fortnight(new DateTime($start));
        $arr = $_POST['arr'] ?? [];
        $dep = $_POST['dep'] ?? [];
        $pause = $_POST['pause'] ?? [];
        $tips = $_POST['tips'] ?? [];
        foreach ($dates as $i => $d) {
            ts_set(
                $timesheet, $emp, $d->format('Y-m-d'),
                $arr[$i] ?? '', $dep[$i] ?? '', $pause[$i] ?? 0, $tips[$i] ?? 0
            );
        }
        data_set('timesheet', $timesheet);
        $flash = 'Heures enregistrées.';
    }
}

// ── Current selection ───────────────────────────────────────────────
$names = array_column($employees, 'name');
$roleOf = [];
foreach ($employees as $e) {
    $roleOf[$e['name']] = $e['role'];
}
$emp = $_REQUEST['emp'] ?? ($names[0] ?? '');
$startStr = $_REQUEST['start'] ?? monday_of(new DateTime())->format('Y-m-d');
$start = new DateTime($startStr);
$dates = fortnight($start);

require_once __DIR__ . '/lib/layout.php';
page_header('Feuille du personnel');
?>
<h1>🗓️ Feuille du personnel</h1>
<?php if ($flash) {
    echo '<p class="ok">' . htmlspecialchars($flash) . '</p>';
} ?>
<?php if ($err) {
    echo '<p class="error">' . htmlspecialchars($err) . '</p>';
} ?>

<details>
    <summary><strong>👤 Gérer les employés (équipe ménage, accueil…)</strong></summary>
    <p style="color:#666">Tous les employés ici comptent leurs heures. La
    répartition des chambres (à venir) ne concernera que l'équipe ménage.</p>
    <form method="post" style="display:flex; gap:10px; align-items:end; flex-wrap:wrap;">
        <input type="hidden" name="action" value="add_emp">
        <div><label>Nom</label><input type="text" name="name" required></div>
        <div><label>Rôle</label><input type="text" name="role" placeholder="ex. Accueil"></div>
        <div><button type="submit">➕ Ajouter</button></div>
    </form>
    <table style="margin-top:12px; max-width:640px;">
        <tr><th>Nom</th><th>Rôle</th><th>Suppr. (mot de passe)</th></tr>
        <?php foreach ($employees as $e) { ?>
            <tr>
                <td><?php echo htmlspecialchars($e['name']); ?></td>
                <td><?php echo htmlspecialchars($e['role'] ?: '—'); ?></td>
                <td>
                    <form method="post" style="display:flex; gap:6px;"
                          onsubmit="return confirm('Supprimer <?php echo htmlspecialchars($e['name']); ?> ?');">
                        <input type="hidden" name="action" value="del_emp">
                        <input type="hidden" name="name" value="<?php echo htmlspecialchars($e['name']); ?>">
                        <input type="password" name="pw" placeholder="mot de passe" style="width:140px">
                        <button type="submit">🗑</button>
                    </form>
                </td>
            </tr>
        <?php } ?>
    </table>
</details>

<hr>

<form method="get" style="display:flex; gap:14px; align-items:end; flex-wrap:wrap;">
    <div>
        <label>Employé</label>
        <select name="emp" onchange="this.form.submit()">
            <?php foreach ($names as $n) {
                $sel = ($n === $emp) ? 'selected' : '';
                echo "<option $sel>" . htmlspecialchars($n) . '</option>';
            } ?>
        </select>
    </div>
    <div>
        <label>Début de la quinzaine</label>
        <input type="date" name="start" value="<?php echo htmlspecialchars($startStr); ?>"
               onchange="this.form.submit()">
    </div>
</form>

<p>Période : <strong><?php echo $dates[0]->format('d/m/Y'); ?> →
   <?php echo $dates[13]->format('d/m/Y'); ?></strong></p>

<form method="post">
    <input type="hidden" name="action" value="save_sheet">
    <input type="hidden" name="emp" value="<?php echo htmlspecialchars($emp); ?>">
    <input type="hidden" name="start" value="<?php echo htmlspecialchars($startStr); ?>">
    <table>
        <tr><th>Jour</th><th>Arrivée</th><th>Départ</th><th>Pause (min)</th>
            <th>Pourboires ($)</th><th>Heures</th></tr>
        <?php
        $totalH = 0.0;
        $totalT = 0.0;
        foreach ($dates as $i => $d) {
            $e = ts_get($timesheet, $emp, $d->format('Y-m-d'));
            $h = worked_hours($e['arrivee'], $e['depart'], $e['pause']);
            $totalH += $h;
            $totalT += $e['tips'];
            ?>
            <tr>
                <td><?php echo fr_weekday($d) . ' ' . $d->format('d/m'); ?></td>
                <td><input type="time" name="arr[<?php echo $i; ?>]" value="<?php echo htmlspecialchars($e['arrivee']); ?>"></td>
                <td><input type="time" name="dep[<?php echo $i; ?>]" value="<?php echo htmlspecialchars($e['depart']); ?>"></td>
                <td><input type="number" min="0" step="5" name="pause[<?php echo $i; ?>]" value="<?php echo (int) $e['pause']; ?>"></td>
                <td><input type="number" min="0" step="0.5" name="tips[<?php echo $i; ?>]" value="<?php echo $e['tips']; ?>"></td>
                <td><?php echo number_format($h, 2); ?> h</td>
            </tr>
        <?php } ?>
    </table>
    <p>
        <button type="submit">💾 Enregistrer</button>
        &nbsp;&nbsp; Total : <strong><?php echo number_format($totalH, 2); ?> h</strong>
        &nbsp;·&nbsp; Pourboires : <strong><?php echo number_format($totalT, 2); ?> $</strong>
    </p>
</form>

<hr>
<h2>Totaux de la quinzaine (tout le personnel)</h2>
<table style="max-width:640px;">
    <tr><th>Employé</th><th>Rôle</th><th>Heures</th><th>Pourboires ($)</th></tr>
    <?php foreach ($names as $n) { ?>
        <tr>
            <td><?php echo htmlspecialchars($n); ?></td>
            <td><?php echo htmlspecialchars($roleOf[$n] ?: '—'); ?></td>
            <td><?php echo number_format(period_total($timesheet, $n, $dates), 2); ?></td>
            <td><?php echo number_format(period_tips($timesheet, $n, $dates), 2); ?></td>
        </tr>
    <?php } ?>
</table>
<p style="margin-top:12px">
    <a href="paie.php?start=<?php echo urlencode($startStr); ?>">
        ⬇️ Télécharger la paie (CSV, ouvrable dans Excel) de la quinzaine
    </a>
</p>
<?php page_footer();
