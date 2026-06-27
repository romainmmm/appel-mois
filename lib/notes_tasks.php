<?php
/** Convertit les notes manuelles (Ménage/Serviette/Chien) d'une date en tâches. */
require_once __DIR__ . '/db.php';

/** Dates (Y-m-d) ayant au moins une note visible sur la feuille. */
function note_dates(): array
{
    $dates = [];
    foreach (data_get('notes', []) as $n) {
        if (in_array($n['type'] ?? '', ['Ménage', 'Serviette', 'Chien'], true)
            && !empty($n['room']) && !empty($n['date'])) {
            $dates[$n['date']] = true;
        }
    }
    return array_keys($dates);
}

/** @return array<array{room:int,floor:int,kind:string,night:string,label:string}> */
function manual_tasks_for_date(string $ymd): array
{
    $notes = data_get('notes', []);
    $out = [];
    foreach ($notes as $n) {
        if (($n['date'] ?? '') !== $ymd) continue;
        if (!in_array($n['type'] ?? '', ['Ménage', 'Serviette', 'Chien'], true)) continue;
        $room = (int)($n['room'] ?? 0);
        if (!$room) continue;
        $label = $n['type'] . (!empty($n['comment']) ? ': ' . $n['comment'] : '');
        $out[] = [
            'room' => $room, 'floor' => intdiv($room, 100) * 100,
            'kind' => 'manuel', 'night' => '', 'label' => $label,
        ];
    }
    return $out;
}
