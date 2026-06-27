<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/pdf_extract.php';
require_once __DIR__ . '/lib/day_parser.php';
require_once __DIR__ . '/lib/room_layout.php';

$data = null;
$err = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['pdf'])) {
    if ($_FILES['pdf']['error'] !== UPLOAD_ERR_OK) {
        $err = 'Échec du téléversement du fichier.';
    } else {
        $tmp = $_FILES['pdf']['tmp_name'];
        try {
            $lines = pdf_lines($tmp);
            $data = parse_day_lines($lines);
        } catch (Throwable $e) {
            $err = 'Erreur de lecture du PDF : ' . $e->getMessage();
        }
    }
}

// Notes manuelles (Serviette/Chien/Ménage) pour la date détectée
$manualNotes = [];
if ($data !== null) {
    $ymd = french_date_to_ymd($data['date'] ?? '');
    if ($ymd) {
        foreach (data_get('notes', []) as $n) {
            if (($n['date'] ?? '') !== $ymd) continue;
            if (!in_array($n['type'] ?? '', ['Ménage', 'Serviette', 'Chien'], true)) continue;
            if (empty($n['room'])) continue;
            $t = mb_strtoupper($n['type'], 'UTF-8') . (!empty($n['comment']) ? ': ' . $n['comment'] : '');
            $manualNotes[(int)$n['room']][] = $t;
        }
        $manualNotes = array_map(fn($a) => implode(' ; ', $a), $manualNotes);
    }
}

require_once __DIR__ . '/lib/layout.php';
page_header('Feuille du jour');
?>
<style>
/* Affichage écran */
.daygrid { border-collapse: collapse; width: 100%; table-layout: fixed; }
.daygrid td { border: 1px solid var(--grid); padding: 4px 6px; font-size: 12px;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.daygrid td.num { width: 36px; text-align: center; font-weight: 700; }
.daygrid td.info { width: 30%; }
.daygrid tr.sep td { border: none; height: 8px; }
.daygrid .depart   { background: #E2C9C4; font-weight: 600; }
.daygrid .arrivee  { background: #D3DAC4; font-weight: 600; }
.daygrid .service  { background: #CBD5DC; font-weight: 600; }
.daygrid .turnover { background: #EAD9B0; font-weight: 600; }
.daygrid .manuel   { background: #C9DCD4; font-weight: 600; }
.legend .manuel { background: #C9DCD4; }
.legend span { display: inline-block; padding: 3px 10px; margin-right: 8px;
    border: 1px solid var(--grid); font-size: 12px; }
.legend .depart{background:#E2C9C4;} .legend .arrivee{background:#D3DAC4;}
.legend .service{background:#CBD5DC;} .legend .turnover{background:#EAD9B0;}
.hors-plan { color: #C00000; font-style: italic; }
@media print {
    @page { size: A4 landscape; margin: 8mm; }
    header.brand, nav.tabs, .noprint { display: none !important; }
    .container { max-width: none; margin: 0; padding: 0; }
    .daygrid td { font-size: 11px; }
}
</style>

<h1 class="noprint">📋 Feuille du jour</h1>

<?php if ($err) {
    echo '<p class="error noprint">' . htmlspecialchars($err) . '</p>';
} ?>

<form method="post" enctype="multipart/form-data" class="noprint"
      style="display:flex; gap:12px; align-items:end; flex-wrap:wrap; margin-bottom:16px;">
    <div>
        <label>PDF « état des chambres »</label>
        <input type="file" name="pdf" accept="application/pdf,.pdf" required>
    </div>
    <button type="submit">Générer la feuille</button>
</form>

<?php if ($data !== null) { ?>
    <div class="noprint" style="margin-bottom:10px;">
        <button onclick="window.print()">🖨️ Imprimer / Enregistrer en PDF</button>
        <span style="margin-left:12px; color:#666;">
            <?php echo (int)(count($data['arrivees'])); ?> arrivée(s),
            <?php echo (int)(count($data['departs'])); ?> départ(s),
            <?php echo (int)(count($data['service'])); ?> service(s)
        </span>
    </div>

    <h2 style="text-align:center; margin:6px 0;">
        Feuille du jour — <?php echo htmlspecialchars($data['date'] ?: 'Date non détectée'); ?>
    </h2>

    <?php echo render_day_grid($data, $manualNotes); ?>

    <p class="legend" style="margin-top:10px;">
        <span class="arrivee">ARRIVÉE</span>
        <span class="depart">DÉPART</span>
        <span class="service">SERVICE</span>
        <span class="turnover">DÉP+ARR</span>
        <span class="manuel">Note (Serviette/Chien…)</span>
    </p>
<?php } else { ?>
    <p class="noprint" style="color:#666;">Dépose le PDF de la journée pour générer
    la feuille (mêmes notations que l'Excel : ARRIVÉE / DÉPART / SERVICE / DÉP+ARR).</p>
<?php } ?>
<?php page_footer();
