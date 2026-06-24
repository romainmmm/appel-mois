<?php
/** Calcul des ménages (départs + services périodiques) à partir des réservations. */

/**
 * @param array $reservations  sortie de parse_reservations_csv()
 * @param int   $freq          ménage de service tous les N nuits (défaut 3)
 * @param ?string $start,$end  bornes (Y-m-d) optionnelles
 * @return array<string, array<array{room:int,floor:int,kind:string,night:string}>>
 *         map date Y-m-d => liste de tâches
 */
function compute_cleanings(array $reservations, int $freq = 3, ?string $start = null, ?string $end = null): array
{
    $sched = [];
    $inRange = function (string $d) use ($start, $end): bool {
        if ($start !== null && $d < $start) return false;
        if ($end !== null && $d > $end) return false;
        return true;
    };
    $add = function (string $d, array $task) use (&$sched, $inRange) {
        if ($inRange($d)) $sched[$d][] = $task;
    };

    foreach ($reservations as $r) {
        // Ménage de départ le jour du départ
        $add($r['checkout'], ['room' => $r['room'], 'floor' => $r['floor'], 'kind' => 'depart', 'night' => '']);

        // Ménages de service tous les $freq nuits, avant le départ
        if ($freq > 0) {
            $ci = new DateTime($r['checkin']);
            $co = new DateTime($r['checkout']);
            $k = 1;
            while (true) {
                $sd = (clone $ci)->modify('+' . ($k * $freq) . ' days');
                if ($sd >= $co) break;
                $add($sd->format('Y-m-d'), [
                    'room' => $r['room'], 'floor' => $r['floor'],
                    'kind' => 'service', 'night' => 'Nuit ' . ($k * $freq),
                ]);
                $k++;
            }
        }
    }

    foreach ($sched as $d => &$tasks) {
        usort($tasks, fn($a, $b) => $a['room'] <=> $b['room']);
    }
    unset($tasks);
    ksort($sched);
    return $sched;
}
