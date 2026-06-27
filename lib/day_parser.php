<?php
/** Analyse les lignes du PDF « état des chambres » en sections. */

function _strip_accents(string $s): string
{
    $from = ['à','â','ä','é','è','ê','ë','î','ï','ô','ö','ù','û','ü','ç','À','Â','Ä','É','È','Ê','Ë','Î','Ï','Ô','Ö','Ù','Û','Ü','Ç'];
    $to   = ['a','a','a','e','e','e','e','i','i','o','o','u','u','u','c','A','A','A','E','E','E','E','I','I','O','O','U','U','U','C'];
    return str_replace($from, $to, $s);
}

function _clean_letters(string $s): string
{
    return strtolower(preg_replace('/[^A-Za-z]/', '', _strip_accents($s)));
}

function _looks_like_date(string $s): bool
{
    $c = _clean_letters($s);
    foreach (['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'] as $j) {
        if (strpos($c, $j) === 0) return true;
    }
    $months = ['janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre'];
    foreach ($months as $m) {
        if (strpos($c, $m) !== false && preg_match('/\d{4}/', $s)) return true;
    }
    return false;
}

function _detect_section(string $s): ?string
{
    $c = _clean_letters($s);
    if (in_array($c, ['arrivees', 'arrives', 'arrivee'], true)) return 'arrivees';
    if (in_array($c, ['departs', 'depart'], true)) return 'departs';
    if ($c === 'service') return 'service';
    return null;
}

function _is_stop(string $s): bool
{
    return in_array(_clean_letters($s), ['notes', 'options'], true);
}

function _clean_date(string $s): string
{
    $t = preg_replace('/\s+/u', '', $s); // ex. "Mercredi16décembre2026"
    $jours = 'lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche';
    $mois = 'janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre';
    if (preg_match('/^(' . $jours . ')(\d{1,2})(' . $mois . ')(\d{4})/ui', $t, $m)) {
        return mb_convert_case($m[1], MB_CASE_TITLE, 'UTF-8') . ' ' . $m[2] . ' '
             . mb_strtolower($m[3], 'UTF-8') . ' ' . $m[4];
    }
    return preg_replace('/\s+/', ' ', trim($s));
}

/** Convertit "Mercredi 16 décembre 2026" -> "2026-12-16" (ou null). */
function french_date_to_ymd(string $label): ?string
{
    $mois = [
        'janvier' => 1, 'février' => 2, 'fevrier' => 2, 'mars' => 3, 'avril' => 4,
        'mai' => 5, 'juin' => 6, 'juillet' => 7, 'août' => 8, 'aout' => 8,
        'septembre' => 9, 'octobre' => 10, 'novembre' => 11, 'décembre' => 12, 'decembre' => 12,
    ];
    if (preg_match('/(\d{1,2})\s+([A-Za-zéûô]+)\s+(\d{4})/u', $label, $m)) {
        $mo = mb_strtolower($m[2], 'UTF-8');
        if (isset($mois[$mo])) {
            return sprintf('%04d-%02d-%02d', (int)$m[3], $mois[$mo], (int)$m[1]);
        }
    }
    return null;
}

function _split_name_extra(string $text): array
{
    if (preg_match('/(Nuit\s*\d+\s*sur\s*\d+)/u', $text, $m)) {
        $extra = preg_replace('/\s+/', ' ', $m[1]);
        $name = trim(str_replace($m[1], '', $text));
        return [$name, $extra];
    }
    return [trim($text), ''];
}

/** @return array{date:string,arrivees:array,departs:array,service:array} */
function parse_day_lines(array $lines): array
{
    $res = ['date' => '', 'arrivees' => [], 'departs' => [], 'service' => []];
    $section = null;
    foreach ($lines as $line) {
        $s = trim($line);
        if ($s === '') continue;

        if ($res['date'] === '' && _looks_like_date($s)) { $res['date'] = _clean_date($s); continue; }

        $sec = _detect_section($s);
        if ($sec) { $section = $sec; continue; }
        if (_is_stop($s)) { $section = null; continue; }

        // Ignorer les références de réservation (58-253531-23771, avec ou sans espace)
        if (preg_match('/^\d{2}-\d{6}-\s*\d{4,5}/', str_replace(' ', '', $s))) continue;

        if ($section && preg_match('/^(\d{3})\s*(.*)$/u', $s, $m)) {
            [$name, $extra] = _split_name_extra(trim($m[2]));
            $res[$section][] = ['room' => (int)$m[1], 'name' => $name, 'extra' => $extra];
        }
    }
    return $res;
}
