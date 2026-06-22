<?php
/** Timesheet helpers (mirror of the Python timesheet logic). */

const FR_WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

function fr_weekday(DateTime $d): string
{
    // PHP: 1 (Mon) .. 7 (Sun)
    return FR_WEEKDAYS[(int) $d->format('N') - 1];
}

function monday_of(DateTime $d): DateTime
{
    $m = clone $d;
    $dow = (int) $m->format('N'); // 1..7
    if ($dow > 1) {
        $m->modify('-' . ($dow - 1) . ' days');
    }
    return $m;
}

/** @return DateTime[] 14 days starting at $start */
function fortnight(DateTime $start): array
{
    $days = [];
    for ($i = 0; $i < 14; $i++) {
        $d = clone $start;
        $d->modify("+$i days");
        $days[] = $d;
    }
    return $days;
}

function worked_hours(?string $arrivee, ?string $depart, $pause = 0): float
{
    if (!$arrivee || !$depart) {
        return 0.0;
    }
    $a = DateTime::createFromFormat('H:i', substr($arrivee, 0, 5));
    $b = DateTime::createFromFormat('H:i', substr($depart, 0, 5));
    if (!$a || !$b) {
        return 0.0;
    }
    $minutes = ($b->getTimestamp() - $a->getTimestamp()) / 60 - (float) $pause;
    if ($minutes <= 0) {
        return 0.0;
    }
    return round($minutes / 60, 2);
}

function ts_get(array $ts, string $emp, string $iso): array
{
    $e = $ts[$emp][$iso] ?? null;
    return [
        'arrivee' => $e['arrivee'] ?? '',
        'depart'  => $e['depart'] ?? '',
        'pause'   => (int) ($e['pause'] ?? 0),
        'tips'    => (float) ($e['tips'] ?? 0),
    ];
}

function ts_set(array &$ts, string $emp, string $iso, string $arr, string $dep, $pause, $tips): void
{
    if (!$arr && !$dep && !$pause && !$tips) {
        unset($ts[$emp][$iso]);
        if (isset($ts[$emp]) && count($ts[$emp]) === 0) {
            unset($ts[$emp]);
        }
        return;
    }
    $ts[$emp][$iso] = [
        'arrivee' => $arr,
        'depart'  => $dep,
        'pause'   => (int) $pause,
        'tips'    => round((float) $tips, 2),
    ];
}

/** @param DateTime[] $dates */
function period_total(array $ts, string $emp, array $dates): float
{
    $t = 0.0;
    foreach ($dates as $d) {
        $e = ts_get($ts, $emp, $d->format('Y-m-d'));
        $t += worked_hours($e['arrivee'], $e['depart'], $e['pause']);
    }
    return round($t, 2);
}

/** @param DateTime[] $dates */
function period_tips(array $ts, string $emp, array $dates): float
{
    $t = 0.0;
    foreach ($dates as $d) {
        $e = ts_get($ts, $emp, $d->format('Y-m-d'));
        $t += $e['tips'];
    }
    return round($t, 2);
}
