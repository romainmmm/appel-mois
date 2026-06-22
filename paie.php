<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/timesheet.php';

$startStr = $_GET['start'] ?? monday_of(new DateTime())->format('Y-m-d');
$start = new DateTime($startStr);
$dates = fortnight($start);

$employees = data_get('employees', []);
$timesheet = data_get('timesheet', []);

$filename = 'Paie_' . $dates[0]->format('Y_m_d') . '_au_' . $dates[13]->format('Y_m_d') . '.csv';
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'w');
// BOM UTF-8 pour qu'Excel affiche bien les accents
fwrite($out, "\xEF\xBB\xBF");

$period = 'Quinzaine du ' . $dates[0]->format('d/m/Y') . ' au ' . $dates[13]->format('d/m/Y');
fputcsv($out, [$period], ';');
fputcsv($out, [], ';');

// Récapitulatif
fputcsv($out, ['Employé', 'Rôle', 'Total heures', 'Total pourboires ($)'], ';');
$gH = 0.0;
$gT = 0.0;
foreach ($employees as $e) {
    $h = period_total($timesheet, $e['name'], $dates);
    $t = period_tips($timesheet, $e['name'], $dates);
    $gH += $h;
    $gT += $t;
    fputcsv($out, [$e['name'], $e['role'], number_format($h, 2, ',', ''), number_format($t, 2, ',', '')], ';');
}
fputcsv($out, ['TOTAL', '', number_format($gH, 2, ',', ''), number_format($gT, 2, ',', '')], ';');

// Détail par jour
fputcsv($out, [], ';');
fputcsv($out, ['Détail par jour'], ';');
fputcsv($out, ['Employé', 'Date', 'Jour', 'Arrivée', 'Départ', 'Pause (min)', 'Heures', 'Pourboires ($)'], ';');
foreach ($employees as $e) {
    foreach ($dates as $d) {
        $en = ts_get($timesheet, $e['name'], $d->format('Y-m-d'));
        $h = worked_hours($en['arrivee'], $en['depart'], $en['pause']);
        if (!$en['arrivee'] && !$en['depart'] && !$h && !$en['tips']) {
            continue;
        }
        fputcsv($out, [
            $e['name'], $d->format('d/m/Y'), fr_weekday($d),
            $en['arrivee'], $en['depart'], $en['pause'],
            number_format($h, 2, ',', ''), number_format($en['tips'], 2, ',', ''),
        ], ';');
    }
}
fclose($out);
