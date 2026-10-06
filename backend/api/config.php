<?php
require __DIR__.'/common.php';
if ($_SERVER['REQUEST_METHOD']!=='GET') { header('Allow: GET'); reply(405,['ok'=>false,'message'=>'Method not allowed']); }
if (!Orders::configured($config)) reply(200,['submissionEnabled'=>false,'consentVersion'=>'2026-10-06']);
try {
    $app=new Orders($config); $app->listing(); // verify schema before enabling UI
    sessionStart();
    $_SESSION['csrf'] ??= bin2hex(random_bytes(32));
    $token=$_SESSION['csrf']; session_write_close();
    reply(200,['submissionEnabled'=>true,'csrfToken'=>$token,'consentVersion'=>$config['consent_version']]);
} catch (Throwable $e) { reply(503,['submissionEnabled'=>false,'message'=>'Приём заявок временно недоступен.']); }
