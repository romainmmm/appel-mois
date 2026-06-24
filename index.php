<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/csv_reservations.php';
require_once __DIR__ . '/lib/schedule.php';
require_once __DIR__ . '/lib/staff_config.php';
require_once __DIR__ . '/lib/distribution.php';
require_once __DIR__ . '/lib/room_layout.php';

auth_start();
$team = load_team();
$err = '';

// Téléversement du CSV des réservations
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['csv'])) {
    if ($_FILES['csv']['error'] !== UPLOAD_ERR_OK) {
        $err = 'Échec du téléversement.';
    } else {
        $freq = max(1, (int)($_POST['freq'] ?? 3));
        try {
            $res = parse_reservations_csv($_FILES['csv']['tmp_name']);
            if (!$res) {
                $err = 'Aucune réservation lue. Vérifie que le fichier est bien le CSV de l\'export.';
            } else {
                $_SESSION['sched'] = compute_cleanings($res, $freq);
                $_SESSION['sched_freq'] = $freq;
                $_SESSION['sched_nres'] = count($res);
            }
        } catch (Throwable $e) {
            $err = 'Erreur de lecture : ' . $e->getMessage();
        }
    }
}

$sched = $_SESSION['sched'] ?? null;
$day = $_GET['day'] ?? null;

require_once __DIR__ . '/lib/layout.php';

// ── Vue imprimable d'une journée ────────────────────────────────────
if ($sched && $day && isset($sched[$day])) {
    $da = assign_day($sched[$day], $team, $day);
    page_header('Feuille du jour — ' . $day);
    $dt = new DateTime($day);
    $label = WEEKDAYS_FR_LONG[(int)$dt->format('N') - 1] . ' ' . $dt->format('d/m/Y');
    echo '<div class="noprint" style="margin-bottom:10px;">';
    echo '<a href="index.php">← Retour au calendrier</a> &nbsp; ';
    echo '<button onclick="window.print()">🖨️ Imprimer / Enregistrer en PDF</button></div>';
    echo '<h2 style="text-align:center;margin:6px 0;">Feuille du jour — ' . htmlspecialchars($label) . '</h2>';
    echo render_assignment_grid($da);
    echo '<p class="legend" style="margin-top:10px;">'
       . '<span class="depart">DÉPART</span><span class="service">SERVICE</span>'
       . '<span class="manager">Gérants (à replanifier)</span></p>';
    page_footer();
    exit;
}

// ── Page principale : import + calendrier ───────────────────────────
page_header('Feuille du mois');
?>
<h1 class="noprint">📅 Feuille du mois</h1>
<?php if ($err) echo '<p class="error noprint">' . htmlspecialchars($err) . '</p>'; ?>

<form method="post" enctype="multipart/form-data" class="noprint"
      style="display:flex; gap:12px; align-items:end; flex-wrap:wrap; margin-bottom:6px;">
    <div>
        <label>Export des réservations (CSV)</label>
        <input type="file" name="csv" accept=".csv,text/csv" required>
    </div>
    <div>
        <label>Ménage de service tous les … jours</label>
        <input type="number" name="freq" min="1" max="14" value="<?php echo (int)($_SESSION['sched_freq'] ?? 3); ?>" style="width:80px">
    </div>
    <button type="submit">Générer le calendrier</button>
</form>
<p class="noprint" style="color:#666;margin-top:0;">
    Astuce : dans Excel, « Enregistrer sous → CSV (séparateur point-virgule) », puis dépose le fichier ici.
</p>

<?php if ($sched) {
    $days = array_keys($sched);
    $ordered = $team;
    usort($ordered, fn($a, $b) => $a['order'] <=> $b['order']);
    ?>
    <p class="noprint"><?php echo (int)($_SESSION['sched_nres'] ?? 0); ?> réservations ·
       <?php echo count($days); ?> jours du <?php echo (new DateTime($days[0]))->format('d/m/Y'); ?>
       au <?php echo (new DateTime(end($days)))->format('d/m/Y'); ?>.
       Clique sur une date pour la feuille imprimable.</p>
    <table class="cal">
        <tr>
            <th>Date</th><th>Jour</th><th>Total</th>
            <?php foreach ($ordered as $w) echo '<th>' . htmlspecialchars($w['name']) . '</th>'; ?>
            <th>Gérants</th>
        </tr>
        <?php foreach ($days as $d) {
            $da = assign_day($sched[$d], $team, $d);
            $dt = new DateTime($d);
            $we = (int)$dt->format('N') >= 6 ? ' class="we"' : '';
            ?>
            <tr<?php echo $we; ?>>
                <td><a href="?day=<?php echo $d; ?>"><?php echo $dt->format('d/m/Y'); ?></a></td>
                <td><?php echo WEEKDAYS_FR_SHORT[(int)$dt->format('N') - 1]; ?></td>
                <td><?php echo count($sched[$d]); ?></td>
                <?php foreach ($ordered as $w) {
                    $n = count($da['assignments'][$w['name']] ?? []);
                    echo '<td>' . ($n ?: '') . '</td>';
                } ?>
                <td<?php echo count($da['unassigned']) ? ' class="over"' : ''; ?>>
                    <?php echo count($da['unassigned']) ?: ''; ?>
                </td>
            </tr>
        <?php } ?>
    </table>
<?php } ?>
<?php page_footer();
