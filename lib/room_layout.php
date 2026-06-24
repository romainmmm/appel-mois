<?php
/** Positions fixes des chambres dans la grille (même plan que la version Excel). */

// room => [ligne, colonne-numéro]  (colonne info = lettre suivante)
const ROOM_POS = [
    // Zone 1 : lignes 2-10
    218 => [2, 'A'], 217 => [3, 'A'], 216 => [4, 'A'], 215 => [5, 'A'], 214 => [6, 'A'],
    213 => [7, 'A'], 212 => [8, 'A'], 211 => [9, 'A'], 210 => [10, 'A'],
    209 => [2, 'C'], 208 => [3, 'C'], 207 => [4, 'C'], 206 => [5, 'C'], 205 => [6, 'C'],
    204 => [7, 'C'], 203 => [8, 'C'], 202 => [9, 'C'], 201 => [10, 'C'],
    109 => [2, 'E'], 108 => [3, 'E'], 107 => [4, 'E'], 106 => [5, 'E'], 105 => [6, 'E'],
    104 => [7, 'E'], 103 => [8, 'E'], 102 => [9, 'E'], 101 => [10, 'E'],
    // Zone 2 : lignes 12-21
    318 => [12, 'A'], 317 => [13, 'A'], 316 => [14, 'A'], 315 => [15, 'A'], 314 => [16, 'A'],
    313 => [17, 'A'], 312 => [18, 'A'], 311 => [19, 'A'], 310 => [20, 'A'],
    309 => [12, 'C'], 308 => [13, 'C'], 307 => [14, 'C'], 306 => [15, 'C'], 305 => [16, 'C'],
    304 => [17, 'C'], 302 => [19, 'C'], 301 => [20, 'C'],
    401 => [12, 'E'], 402 => [13, 'E'], 403 => [14, 'E'], 404 => [15, 'E'], 406 => [16, 'E'],
    407 => [17, 'E'], 408 => [18, 'E'], 411 => [19, 'E'], 412 => [20, 'E'], 414 => [21, 'E'],
];

/** Construit, pour une journée analysée, le HTML de la grille imprimable. */
function render_day_grid(array $data): string
{
    // room => liste de tâches
    $tasks = [];
    foreach (['arrivee' => 'arrivees', 'depart' => 'departs', 'service' => 'service'] as $kind => $key) {
        foreach ($data[$key] as $e) {
            $tasks[$e['room']][] = ['kind' => $kind] + $e;
        }
    }

    // pos[ligne][col] = room
    $grid = [];
    foreach (ROOM_POS as $room => [$row, $col]) { $grid[$row][$col] = $room; }

    $cell = function (?int $room) use ($tasks): string {
        if ($room === null) return '<td class="num"></td><td class="info"></td>';
        $num = '<td class="num">' . $room . '</td>';
        if (empty($tasks[$room])) return $num . '<td class="info"></td>';
        $kinds = array_column($tasks[$room], 'kind');
        $names = [];
        foreach ($tasks[$room] as $t) { if (trim($t['name']) !== '') $names[$t['name']] = true; }
        $names = implode(' / ', array_keys($names));
        if (in_array('depart', $kinds, true) && in_array('arrivee', $kinds, true)) {
            $cls = 'turnover'; $label = 'DÉP+ARR';
        } elseif (in_array('depart', $kinds, true)) {
            $cls = 'depart'; $label = 'DÉPART';
        } elseif (in_array('arrivee', $kinds, true)) {
            $cls = 'arrivee'; $label = 'ARRIVÉE';
        } else {
            $cls = 'service'; $label = 'SERVICE';
        }
        $extra = '';
        foreach ($tasks[$room] as $t) { if (!empty($t['extra'])) { $extra = ' (' . $t['extra'] . ')'; break; } }
        $txt = htmlspecialchars($label . ' | ' . $names . $extra);
        return $num . '<td class="info ' . $cls . '">' . $txt . '</td>';
    };

    $rowsZone1 = range(2, 10);
    $rowsZone2 = range(12, 21);
    $html = '<table class="daygrid">';
    foreach ([$rowsZone1, $rowsZone2] as $zi => $zone) {
        if ($zi === 1) $html .= '<tr class="sep"><td colspan="6"></td></tr>';
        foreach ($zone as $r) {
            $html .= '<tr>';
            foreach (['A', 'C', 'E'] as $col) {
                $html .= $cell($grid[$r][$col] ?? null);
            }
            $html .= '</tr>';
        }
    }
    $html .= '</table>';

    // Chambres hors plan (sécurité)
    $extras = array_diff(array_keys($tasks), array_keys(ROOM_POS));
    if ($extras) {
        sort($extras);
        $html .= '<p class="hors-plan">Chambres hors plan : ' . implode(', ', $extras) . '</p>';
    }
    return $html;
}

/** Grille imprimable d'une journée du calendrier mensuel (avec préposée par chambre). */
function render_assignment_grid(array $da): string
{
    $roomMap = []; // room => [kind, worker, night]
    foreach ($da['assignments'] as $worker => $tasks) {
        foreach ($tasks as $t) { $roomMap[$t['room']] = [$t['kind'], $worker, $t['night'] ?? '']; }
    }
    foreach ($da['unassigned'] as $t) { $roomMap[$t['room']] = [$t['kind'], 'Gérants', $t['night'] ?? '']; }

    $grid = [];
    foreach (ROOM_POS as $room => [$row, $col]) { $grid[$row][$col] = $room; }

    $cell = function (?int $room) use ($roomMap): string {
        if ($room === null) return '<td class="num"></td><td class="info"></td>';
        $num = '<td class="num">' . $room . '</td>';
        if (!isset($roomMap[$room])) return $num . '<td class="info"></td>';
        [$kind, $worker, $night] = $roomMap[$room];
        $label = ($kind === 'depart') ? 'DÉPART' : 'SERVICE';
        $cls = ($worker === 'Gérants') ? 'manager' : ($kind === 'depart' ? 'depart' : 'service');
        $txt = $label . ' | ' . $worker . ($night ? ' (' . $night . ')' : '');
        return $num . '<td class="info ' . $cls . '">' . htmlspecialchars($txt) . '</td>';
    };

    $html = '<table class="daygrid">';
    foreach ([range(2, 10), range(12, 21)] as $zi => $zone) {
        if ($zi === 1) $html .= '<tr class="sep"><td colspan="6"></td></tr>';
        foreach ($zone as $r) {
            $html .= '<tr>';
            foreach (['A', 'C', 'E'] as $col) { $html .= $cell($grid[$r][$col] ?? null); }
            $html .= '</tr>';
        }
    }
    $html .= '</table>';

    $extras = array_diff(array_keys($roomMap), array_keys(ROOM_POS));
    if ($extras) {
        sort($extras);
        $html .= '<p class="hors-plan">Chambres hors plan : ' . implode(', ', $extras) . '</p>';
    }
    return $html;
}
