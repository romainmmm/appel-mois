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

/** @return array<array{username:string,role:string}> */
function all_users(): array
{
    return db()->query('SELECT username, role FROM users ORDER BY role, username')->fetchAll();
}

function count_gerants(): int
{
    return (int) db()->query("SELECT COUNT(*) FROM users WHERE role = 'gerant'")->fetchColumn();
}

function delete_user(string $username): void
{
    db()->prepare('DELETE FROM users WHERE username = ?')->execute([$username]);
}

function set_password(string $username, string $password): void
{
    $sql = 'UPDATE users SET pass_hash = ? WHERE username = ?';
    db()->prepare($sql)->execute([password_hash($password, PASSWORD_DEFAULT), $username]);
}
