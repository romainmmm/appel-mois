<?php
require_once __DIR__ . '/lib/auth.php';
require_login();
require_once __DIR__ . '/lib/layout.php';
page_header('Feuille du mois');
?>
<h1>Tableau de bord</h1>
<p>Bienvenue, <strong><?php echo htmlspecialchars(current_user()['username']); ?></strong>.</p>
<p>La version web (PHP + MySQL) est en cours de construction. Les sections
arrivent ici, avec des <strong>données partagées</strong> entre tous les postes.</p>
<ul>
    <li>📅 Feuille du mois — répartition des ménages (à venir)</li>
    <li>📋 Feuille du jour — à partir du PDF (à venir)</li>
    <li>📝 Notes / tâches manuelles (à venir)</li>
    <li>🗓️ Feuille du personnel — heures et pourboires (à venir)</li>
</ul>
<?php page_footer();
