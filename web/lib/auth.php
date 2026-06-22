<?php
require_once __DIR__ . '/db.php';

function auth_start(): void
{
    if (session_status() !== PHP_SESSION_ACTIVE) {
        session_start();
    }
}

function users_count(): int
{
    return (int) db()->query('SELECT COUNT(*) FROM users')->fetchColumn();
}

function create_user(string $username, string $password, string $role): void
{
    $sql = 'INSERT INTO users (username, pass_hash, role) VALUES (?, ?, ?)';
    db()->prepare($sql)->execute([
        $username, password_hash($password, PASSWORD_DEFAULT), $role,
    ]);
}

function find_user(string $username)
{
    $st = db()->prepare('SELECT * FROM users WHERE username = ?');
    $st->execute([$username]);
    return $st->fetch();
}

function login(string $username, string $password): bool
{
    $row = find_user($username);
    if ($row && password_verify($password, $row['pass_hash'])) {
        auth_start();
        session_regenerate_id(true);
        $_SESSION['user'] = ['username' => $row['username'], 'role' => $row['role']];
        return true;
    }
    return false;
}

function logout(): void
{
    auth_start();
    $_SESSION = [];
    session_destroy();
}

function current_user()
{
    auth_start();
    return $_SESSION['user'] ?? null;
}

function require_login(): void
{
    if (!current_user()) {
        header('Location: login.php');
        exit;
    }
}

function is_gerant(): bool
{
    $u = current_user();
    return $u && $u['role'] === 'gerant';
}
