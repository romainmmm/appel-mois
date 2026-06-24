<?php
/** Configuration de l'équipe ménage (ordre, étage, plafonds, congés) pour la répartition. */
require_once __DIR__ . '/db.php';

// jours : 0=Lundi ... 6=Dimanche
const WEEKDAYS_FR_SHORT = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
const WEEKDAYS_FR_LONG  = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

function default_team(): array
{
    $every = fn($n) => [0 => $n, 1 => $n, 2 => $n, 3 => $n, 4 => $n, 5 => $n, 6 => $n];
    return [
        ['name' => 'Anna', 'order' => 1, 'home_floor' => 100, 'floor_strict' => true,
         'weekly_max' => [0 => 5, 2 => 5, 4 => 5, 3 => 8, 5 => 8, 6 => 8], 'days_off' => []],
        ['name' => 'Isabelle', 'order' => 2, 'home_floor' => 200, 'floor_strict' => false,
         'weekly_max' => $every(13), 'days_off' => []],
        ['name' => 'Oumar', 'order' => 3, 'home_floor' => null, 'floor_strict' => false,
         'weekly_max' => $every(10), 'days_off' => []],
        ['name' => 'Morgann', 'order' => 4, 'home_floor' => null, 'floor_strict' => false,
         'weekly_max' => $every(6), 'days_off' => []],
        ['name' => 'Estrella', 'order' => 5, 'home_floor' => null, 'floor_strict' => false,
         'weekly_max' => $every(6), 'days_off' => []],
        ['name' => 'Fatoumata', 'order' => 6, 'home_floor' => null, 'floor_strict' => false,
         'weekly_max' => $every(8), 'days_off' => []],
        ['name' => 'Chantale', 'order' => 7, 'home_floor' => null, 'floor_strict' => false,
         'weekly_max' => $every(10), 'days_off' => []],
    ];
}

function load_team(): array
{
    $t = data_get('staff_config', null);
    if ($t === null) return default_team();
    // normaliser les clés weekly_max en entiers
    foreach ($t as &$w) {
        $wm = [];
        foreach (($w['weekly_max'] ?? []) as $k => $v) { $wm[(int)$k] = (int)$v; }
        $w['weekly_max'] = $wm;
        $w['days_off'] = $w['days_off'] ?? [];
        $w['home_floor'] = isset($w['home_floor']) ? $w['home_floor'] : null;
        $w['floor_strict'] = !empty($w['floor_strict']);
    }
    return $t;
}

function save_team(array $team): void
{
    data_set('staff_config', $team);
}

/** Plafond de chambres d'un préposé pour une date (0 = indisponible). */
function worker_max_on(array $w, string $ymd): int
{
    if (in_array($ymd, $w['days_off'] ?? [], true)) return 0;
    $wd = (int)(new DateTime($ymd))->format('N') - 1; // 0=Lundi
    return (int)($w['weekly_max'][$wd] ?? 0);
}
