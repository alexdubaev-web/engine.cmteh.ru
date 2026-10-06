<?php
declare(strict_types=1);
ini_set('display_errors','0');
require_once __DIR__.'/../../backend/app.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Robots-Tag: noindex, nofollow');
function reply(int $status, array $data): never { http_response_code($status); echo json_encode($data,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR); exit; }
$configPath=__DIR__.'/../../backend/config.php';
$config=is_file($configPath) ? require $configPath : [];
function sessionStart(): void {
    ini_set('session.use_strict_mode','1');
    session_name('cm_session');
    session_set_cookie_params(['lifetime'=>0,'path'=>'/api/','secure'=>true,'httponly'=>true,'samesite'=>'Strict']);
    session_start();
}
