<?php
/**
 * Extraction de texte d'un PDF (gère les polices CID via ToUnicode).
 * Conçu pour les PDF « état des chambres » de Reservit. Pur PHP (mbstring + zlib).
 * Retourne une liste de lignes de texte.
 */
function pdf_lines(string $path): array
{
    $raw = file_get_contents($path);

    preg_match_all('/(\d+)\s+0\s+obj(.*?)endobj/s', $raw, $om, PREG_SET_ORDER);
    $objText = [];
    foreach ($om as $o) { $objText[(int)$o[1]] = $o[2]; }

    $objStream = [];
    foreach ($objText as $num => $t) {
        if (preg_match('/stream\r?\n(.*?)\r?\nendstream/s', $t, $sm)) {
            $u = @gzuncompress($sm[1]);
            $objStream[$num] = ($u !== false) ? $u : $sm[1];
        }
    }

    $parseCMap = function (string $s): array {
        $map = [];
        if (preg_match_all('/beginbfchar(.*?)endbfchar/s', $s, $bc)) {
            foreach ($bc[1] as $blk) {
                preg_match_all('/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/', $blk, $p, PREG_SET_ORDER);
                foreach ($p as $x) { $map[strtoupper($x[1])] = hexdec(substr($x[2], 0, 4)); }
            }
        }
        if (preg_match_all('/beginbfrange(.*?)endbfrange/s', $s, $br)) {
            foreach ($br[1] as $blk) {
                preg_match_all('/<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>/', $blk, $r, PREG_SET_ORDER);
                foreach ($r as $x) {
                    $lo = hexdec($x[1]); $hi = hexdec($x[2]); $dst = hexdec(substr($x[3], 0, 4));
                    for ($c = $lo; $c <= $hi; $c++) {
                        $map[strtoupper(str_pad(dechex($c), 4, '0', STR_PAD_LEFT))] = $dst + ($c - $lo);
                    }
                }
            }
        }
        return $map;
    };

    $cmapByFontObj = [];
    foreach ($objText as $num => $t) {
        if (preg_match('/\/ToUnicode\s+(\d+)\s+0\s+R/', $t, $mm)) {
            $tuObj = (int)$mm[1];
            if (isset($objStream[$tuObj])) { $cmapByFontObj[$num] = $parseCMap($objStream[$tuObj]); }
        }
    }
    $cmapByName = [];
    if (preg_match_all('#/(F\d+)\s+(\d+)\s+0\s+R#', $raw, $fm, PREG_SET_ORDER)) {
        foreach ($fm as $x) {
            $obj = (int)$x[2];
            if (isset($cmapByFontObj[$obj])) { $cmapByName[$x[1]] = $cmapByFontObj[$obj]; }
        }
    }

    $decode = function (string $hex, array $map): string {
        $out = '';
        for ($i = 0; $i + 4 <= strlen($hex); $i += 4) {
            $cid = strtoupper(substr($hex, $i, 4));
            if (isset($map[$cid])) { $out .= mb_chr($map[$cid], 'UTF-8'); }
        }
        return $out;
    };

    $fragments = [];
    foreach ($objStream as $num => $s) {
        if (strpos($s, 'Tj') === false) continue;
        if (strpos($s, 'beginbfchar') !== false) continue;

        $events = [];
        if (preg_match_all('#/(F\d+)\s+[\d.]+\s+Tf#', $s, $mm, PREG_OFFSET_CAPTURE | PREG_SET_ORDER)) {
            foreach ($mm as $x) { $events[] = [$x[0][1], 'font', $x[1][0]]; }
        }
        if (preg_match_all('#[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s+([-\d.]+)\s+([-\d.]+)\s+Tm#', $s, $mm, PREG_OFFSET_CAPTURE | PREG_SET_ORDER)) {
            foreach ($mm as $x) { $events[] = [$x[0][1], 'tm', [(float)$x[1][0], (float)$x[2][0]]]; }
        }
        if (preg_match_all('#([-\d.]+)\s+([-\d.]+)\s+Td#', $s, $mm, PREG_OFFSET_CAPTURE | PREG_SET_ORDER)) {
            foreach ($mm as $x) { $events[] = [$x[0][1], 'td', [(float)$x[1][0], (float)$x[2][0]]]; }
        }
        if (preg_match_all('#<([0-9A-Fa-f]+)>\s*Tj#', $s, $mm, PREG_OFFSET_CAPTURE | PREG_SET_ORDER)) {
            foreach ($mm as $x) { $events[] = [$x[0][1], 'tj', $x[1][0]]; }
        }
        usort($events, fn($a, $b) => $a[0] <=> $b[0]);

        $curMap = []; $x = 0; $y = 0;
        foreach ($events as $e) {
            if ($e[1] === 'font') { $curMap = $cmapByName[$e[2]] ?? []; }
            elseif ($e[1] === 'tm') { $x = $e[2][0]; $y = $e[2][1]; }
            elseif ($e[1] === 'td') { $x += $e[2][0]; $y += $e[2][1]; }
            elseif ($e[1] === 'tj') {
                $txt = $decode($e[2], $curMap);
                if (trim($txt) !== '') { $fragments[] = [$y, $x, $txt]; }
            }
        }
    }

    usort($fragments, fn($a, $b) => ($a[0] <=> $b[0]) ?: ($a[1] <=> $b[1]));
    $lines = []; $curY = null; $buf = ''; $prevX = 0;
    foreach ($fragments as $f) {
        if ($curY === null || abs($f[0] - $curY) > 4) {
            if (trim($buf) !== '') $lines[] = trim($buf);
            $buf = $f[2]; $curY = $f[0]; $prevX = $f[1];
        } else {
            $buf .= (($f[1] - $prevX) > 25 ? ' ' : '') . $f[2];
            $prevX = $f[1];
        }
    }
    if (trim($buf) !== '') $lines[] = trim($buf);
    return $lines;
}
