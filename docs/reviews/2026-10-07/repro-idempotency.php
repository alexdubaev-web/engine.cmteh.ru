<?php
declare(strict_types=1);
$repo=dirname(__DIR__,3);
$case=sys_get_temp_dir().'/cmteh-idempotency-'.bin2hex(random_bytes(8));
if (!mkdir($case,0700)) throw new RuntimeException('Cannot create audit fixture');
copy($repo.'/backend/app.php',$case.'/app.php');
copy($repo.'/backend/catalog.json',$case.'/catalog.json');
try {
    require $case.'/app.php';
    $c=['key'=>str_repeat('ab',32),'consent_version'=>'2026-10-06','rate_limit'=>8,'retention_days'=>90];
    $db=new PDO('sqlite::memory:');$a=new Orders($c,$db);$a->migrate();
    $catalog=json_decode(file_get_contents($case.'/catalog.json'),true,512,JSON_THROW_ON_ERROR);$p=$catalog[0];
    $d=['requestId'=>'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','name'=>'Audit User','contact'=>'audit@example.ru','comment'=>'audit order','website'=>'','consent'=>true,'consentVersion'=>'2026-10-06','items'=>[['id'=>$p['id'],'quantity'=>1]]];
    $a->accept($d,'127.0.0.1','audit consent');
    $catalog[0]['price']++;file_put_contents($case.'/catalog.json',json_encode($catalog,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR));
    $b=new Orders($c,$db);
    try {$b->accept($d,'127.0.0.1','audit consent');echo "RETRY_ACCEPTED\n";}
    catch (ApiError $e) {echo "RETRY_ERROR status={$e->status}\n";}
} finally {
    unlink($case.'/app.php');unlink($case.'/catalog.json');rmdir($case);
}
