<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/layout.php';
page_header(ucfirst('personnel'));
echo '<h1>Section « personnel »</h1><p>En cours de construction (version web).</p>';
page_footer();
