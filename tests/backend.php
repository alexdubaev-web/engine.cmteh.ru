<?php
declare(strict_types=1);
require __DIR__.'/../backend/app.php';
function check(bool $ok,string $message): void { if (!$ok) throw new RuntimeException($message); echo "PASS $message\n"; }
function rejects(callable $fn,int $status,string $message): void { try { $fn(); } catch (ApiError $e) { check($e->status===$status,$message); return; } throw new RuntimeException('Expected rejection: '.$message); }
$c=['key'=>str_repeat('ab',32),'consent_version'=>'2026-10-04','rate_limit'=>2,'retention_days'=>90];
$db=new PDO(getenv('CM_TEST_DSN') ?: 'sqlite::memory:',getenv('CM_TEST_DB_USER') ?: null,getenv('CM_TEST_DB_PASSWORD') ?: null);$app=new Orders($c,$db);$app->migrate();
$p=json_decode(file_get_contents(__DIR__.'/../backend/catalog.json'),true)[0];
$d=['requestId'=>'11111111-1111-4111-8111-111111111111','name'=>'Тест','contact'=>'test@example.ru','comment'=>'Тестовая заявка','website'=>'','consent'=>true,'consentVersion'=>'2026-10-04','items'=>[['id'=>$p['id'],'quantity'=>2,'price'=>1]]];
rejects(fn()=>$app->accept(array_replace($d,['consent'=>false]),'127.0.0.1','consent'),400,'consent required');
rejects(fn()=>$app->accept(array_replace($d,['consentVersion'=>'old']),'127.0.0.1','consent'),400,'consent version required');
rejects(fn()=>$app->accept(array_replace($d,['contact'=>"a@example.ru\r\nBcc: x@example.ru"]),'127.0.0.1','consent'),400,'header injection rejected');
rejects(fn()=>$app->accept(array_replace($d,['website'=>'bot']),'127.0.0.1','consent'),400,'honeypot rejected');
rejects(fn()=>$app->accept(array_replace($d,['items'=>[['id'=>'nonexistent','quantity'=>1]]]),'127.0.0.1','consent'),400,'unknown products rejected');
rejects(fn()=>$app->accept(array_replace($d,['items'=>[['id'=>$p['id'],'quantity'=>0]]]),'127.0.0.1','consent'),400,'invalid quantity rejected');
check($app->accept($d,'127.0.0.1','approved document')['ok'],'valid order stored');
$payload=$app->export($d['requestId']);check($payload['total']===$p['price']*2,'server catalog sets price');
check($payload['consent']['sha256']===hash('sha256','approved document') && $payload['consent']['given'],'consent evidence persisted');
check(!str_contains($db->query('SELECT payload FROM orders')->fetchColumn(),'test@example.ru'),'PII encrypted in database');
check($app->accept($d,'127.0.0.1','approved document')['ok'] && count($app->listing())===1,'retry idempotent');
rejects(fn()=>$app->accept(array_replace($d,['comment'=>'Changed']),'127.0.0.1','consent'),409,'id reuse with changed data rejected');
$d2=array_replace($d,['requestId'=>'22222222-2222-4222-8222-222222222222','items'=>[]]);check($app->accept($d2,'127.0.0.1','consent')['ok'],'inquiry accepted without products');
rejects(fn()=>$app->accept(array_replace($d,['requestId'=>'33333333-3333-4333-8333-333333333333']),'127.0.0.1','consent'),429,'persistent rate limit enforced');
$r=$app->deliver(function(){throw new RuntimeException('SMTP unavailable');});check($r['retry']===2 && count($app->listing())===2,'SMTP failure preserves orders');
$db->exec('UPDATE orders SET next_attempt=0');$sent=[];
$r=$app->deliver(function($id,$body)use(&$sent){$sent[]=$id;check(isset($body['contact']),'outbox decrypts mail content');});check($r['sent']===2,'outbox retries successfully');
check($app->deliver(fn()=>throw new RuntimeException('duplicate'))['sent']===0,'sent mail not resent');
check($app->delete($d2['requestId'])===1,'individual deletion');
$db->exec('UPDATE orders SET created_at=1');check($app->purge()===1 && !$app->listing(),'retention deletes payload and consent');
check(!Orders::configured([]),'unconfigured backend stays disabled');
echo "Backend checks complete\n";
