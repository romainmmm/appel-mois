<?php
/** Lecture de l'export de réservations enregistré en CSV (depuis Excel). */

function _parse_date_ymd(string $s): ?string
{
    $s = trim($s);
    if ($s === '') return null;
    $datePart = preg_split('/[ T]/', $s)[0];
    if (strpos($datePart, '-') !== false) {
        $d = DateTime::createFromFormat('Y-m-d', $datePart);
    } elseif (strpos($datePart, '/') !== false) {
        $d = DateTime::createFromFormat('d/m/Y', $datePart);   // format français
    } else {
        return null;
    }
    return $d ? $d->format('Y-m-d') : null;
}

/**
 * Colonnes (positions fixes de l'export Reservit) :
 * 0 = n° réservation, 1 = n° chambre, 4 = statut, 8 = date début, 9 = date départ.
 * @return array<array{booking:string,room:int,floor:int,checkin:string,checkout:string}>
 */
function parse_reservations_csv(string $path, bool $confirmedOnly = true): array
{
    $raw = file_get_contents($path);
    $raw = preg_replace('/^\xEF\xBB\xBF/', '', $raw); // enlever le BOM éventuel
    $lines = preg_split('/\r\n|\r|\n/', $raw);
    if (count($lines) < 2) return [];

    $delim = (substr_count($lines[0], ';') >= substr_count($lines[0], ',')) ? ';' : ',';

    $out = [];
    for ($i = 1; $i < count($lines); $i++) {
        if (trim($lines[$i]) === '') continue;
        $c = str_getcsv($lines[$i], $delim);
        if (count($c) < 10) continue;

        $roomRaw = trim($c[1]);
        if ($roomRaw === '' || !is_numeric(str_replace(',', '.', $roomRaw))) continue;
        $room = (int)(float)str_replace(',', '.', $roomRaw);
        if ($room < 100 || $room > 999) continue;

        $status = trim($c[4]);
        if ($confirmedOnly && stripos($status, 'annul') !== false) continue;

        $checkin = _parse_date_ymd($c[8]);
        $checkout = _parse_date_ymd($c[9]);
        if (!$checkin || !$checkout || $checkin >= $checkout) continue;

        $out[] = [
            'booking'  => trim($c[0]),
            'room'     => $room,
            'floor'    => intdiv($room, 100) * 100,
            'checkin'  => $checkin,
            'checkout' => $checkout,
        ];
    }
    return $out;
}
