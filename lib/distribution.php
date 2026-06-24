<?php
/** Répartition des ménages d'une journée entre les préposés (modèle « draft »). */
require_once __DIR__ . '/staff_config.php';

/**
 * @param array  $tasks   tâches du jour (room, floor, kind, night)
 * @param array  $team    config des préposés (load_team)
 * @param string $ymd     date Y-m-d
 * @return array{assignments: array<string,array>, unassigned: array}
 */
function assign_day(array $tasks, array $team, string $ymd): array
{
    usort($team, fn($a, $b) => $a['order'] <=> $b['order']);

    $assign = [];
    $cap = [];
    foreach ($team as $w) {
        $assign[$w['name']] = [];
        $cap[$w['name']] = worker_max_on($w, $ymd);
    }
    $remaining = array_values($tasks);

    // Passe 1 : étage attitré
    foreach ($team as $w) {
        if ($cap[$w['name']] <= 0 || $w['home_floor'] === null) continue;
        foreach ($remaining as $i => $t) {
            if ($cap[$w['name']] <= 0) break;
            if ($t['floor'] === $w['home_floor']) {
                $assign[$w['name']][] = $t;
                $cap[$w['name']]--;
                unset($remaining[$i]);
            }
        }
        $remaining = array_values($remaining);
    }

    // Passe 2 : reste, dans l'ordre, regroupé par étage
    foreach ($team as $w) {
        if ($cap[$w['name']] <= 0) continue;
        usort($remaining, fn($a, $b) => ($a['floor'] <=> $b['floor']) ?: ($a['room'] <=> $b['room']));
        foreach ($remaining as $i => $t) {
            if ($cap[$w['name']] <= 0) break;
            if ($w['floor_strict'] && $t['floor'] !== $w['home_floor']) continue;
            $assign[$w['name']][] = $t;
            $cap[$w['name']]--;
            unset($remaining[$i]);
        }
        $remaining = array_values($remaining);
    }

    return ['assignments' => $assign, 'unassigned' => array_values($remaining)];
}
