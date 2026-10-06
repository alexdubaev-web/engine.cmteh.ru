<?php
require __DIR__.'/common.php';
if ($_SERVER['REQUEST_METHOD']!=='POST') { header('Allow: POST'); reply(405,['ok'=>false,'message'=>'Method not allowed']); }
// Fail closed, before reading the request body.
if (!Orders::configured($config)) reply(503,['ok'=>false,'message'=>'Приём заявок пока не подключён.']);
if (($_SERVER['HTTP_ORIGIN'] ?? '')!==$config['origin']) reply(403,['ok'=>false,'message'=>'Обновите страницу и повторите отправку.']);
if (!str_starts_with(strtolower($_SERVER['CONTENT_TYPE'] ?? ''),'application/json')) reply(415,['ok'=>false,'message'=>'Ожидается JSON.']);
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0)>24576) reply(413,['ok'=>false,'message'=>'Заявка слишком большая.']);
sessionStart();
$token=$_SESSION['csrf'] ?? ''; session_write_close();
if (!$token || !hash_equals($token,$_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) reply(403,['ok'=>false,'message'=>'Обновите страницу и подтвердите согласие.']);
$raw=file_get_contents('php://input',false,null,0,24577);
if (strlen($raw)>24576) reply(413,['ok'=>false,'message'=>'Заявка слишком большая.']);
try {
    $data=json_decode($raw,true,64,JSON_THROW_ON_ERROR);
    if (!is_array($data) || array_is_list($data)) throw new ApiError(400,'Проверьте заявку.');
    $app=new Orders($config);
    $result=$app->accept($data,$_SERVER['REMOTE_ADDR'] ?? 'unknown',file_get_contents(__DIR__.'/../consent/index.html'));
    // The response acknowledges durable storage, not guaranteed email delivery.
    if ($config['immediate_delivery'] ?? false) $app->deliver([$app,'sendMail'],1);
    reply(200,$result);
} catch (ApiError $e) { if ($e->status===429) header('Retry-After: 900'); reply($e->status,['ok'=>false,'message'=>$e->getMessage()]); }
catch (JsonException $e) { reply(400,['ok'=>false,'message'=>'Некорректная заявка.']); }
catch (Throwable $e) { reply(503,['ok'=>false,'message'=>'Не удалось зарегистрировать заявку. Повторите попытку или сохраните её в файл.']); }
