<?php
require_once __DIR__ . '/../config.php';

/** Single shared PDO connection (MySQL on the host, SQLite locally). */
function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    if (DB_DRIVER === 'sqlite') {
        @mkdir(dirname(DB_SQLITE), 0775, true);
        $pdo = new PDO('sqlite:' . DB_SQLITE);
        $pdo->exec('PRAGMA journal_mode=WAL');
    } else {
        $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4';
        $pdo = new PDO($dsn, DB_USER, DB_PASS);
    }
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    init_schema($pdo);
    return $pdo;
}

function init_schema(PDO $pdo): void
{
    $pdo->exec(
        "CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(64) PRIMARY KEY,
            pass_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL
        )"
    );
    $pdo->exec(
        "CREATE TABLE IF NOT EXISTS app_data (
            k VARCHAR(64) PRIMARY KEY,
            v MEDIUMTEXT
        )"
    );
}

/** Read a JSON document from app_data. */
function data_get(string $key, $default = null)
{
    $st = db()->prepare('SELECT v FROM app_data WHERE k = ?');
    $st->execute([$key]);
    $row = $st->fetchColumn();
    if ($row === false) {
        return $default;
    }
    return json_decode($row, true);
}

/** Write a JSON document to app_data (upsert). */
function data_set(string $key, $value): void
{
    $json = json_encode($value, JSON_UNESCAPED_UNICODE);
    if (DB_DRIVER === 'mysql') {
        $sql = 'INSERT INTO app_data (k, v) VALUES (?, ?)
                ON DUPLICATE KEY UPDATE v = VALUES(v)';
    } else {
        $sql = 'INSERT INTO app_data (k, v) VALUES (?, ?)
                ON CONFLICT(k) DO UPDATE SET v = excluded.v';
    }
    db()->prepare($sql)->execute([$key, $json]);
}
