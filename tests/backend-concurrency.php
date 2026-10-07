<?php
declare(strict_types=1);
require __DIR__.'/../backend/app.php';
function concurrencyCheck(bool $ok,string $message): void { if (!$ok) throw new RuntimeException($message); echo "PASS $message\n"; }
if (!function_exists('pcntl_fork')) { echo "SKIP pcntl unavailable\n"; exit(0); }
$root=sys_get_temp_dir().'/engine-orders-concurrency-'.bin2hex(random_bytes(8));
if (!mkdir($root,0700)) throw new RuntimeException('Could not create isolated concurrency directory');
$path=$root.'/orders.sqlite';$config=['key'=>str_repeat('ab',32),'consent_version'=>'2026-10-06','rate_limit'=>100,'retention_days'=>90];
$db=new PDO('sqlite:'.$path);$app=new Orders($config,$db);$app->migrate();$db=null;$app=null;
$workers=8;$children=[];
for ($i=1;$i<=$workers;$i++) {
    $pid=pcntl_fork();if ($pid===-1) throw new RuntimeException('Could not fork concurrency worker');
    if ($pid===0) {
        try {
            $childDb=new PDO('sqlite:'.$path);$child=new Orders($config,$childDb);
            $id=sprintf('00000000-0000-4000-8000-%012d',$i);
            $result=$child->accept(['requestId'=>$id,'name'=>'Клиент '.$i,'contact'=>'test@example.ru','comment'=>'Тест параллельной заявки','website'=>'','consent'=>true,'consentVersion'=>$config['consent_version'],'items'=>[]],'127.0.0.'.$i,'isolated consent');
            file_put_contents($root.'/result-'.$i,json_encode($result,JSON_THROW_ON_ERROR),LOCK_EX);exit(0);
        } catch (Throwable $e) { file_put_contents($root.'/result-'.$i,json_encode(['error'=>$e->getMessage()]),LOCK_EX);exit(1); }
    }
    $children[$i]=$pid;
}
foreach ($children as $i=>$pid) { pcntl_waitpid($pid,$status);concurrencyCheck(pcntl_wifexited($status)&&pcntl_wexitstatus($status)===0,'concurrent worker '.$i.' accepted'); }
$db=new PDO('sqlite:'.$path);$app=new Orders($config,$db);$numbers=[];
for ($i=1;$i<=$workers;$i++) {
    $result=json_decode((string)file_get_contents($root.'/result-'.$i),true,512,JSON_THROW_ON_ERROR);
    if (isset($result['error'])) throw new RuntimeException('Concurrent worker failed: '.$result['error']);
    $numbers[]=$result['orderNumber'];$id=sprintf('00000000-0000-4000-8000-%012d',$i);
    $replay=$app->accept(['requestId'=>$id,'name'=>'Клиент '.$i,'contact'=>'test@example.ru','comment'=>'Тест параллельной заявки','website'=>'','consent'=>true,'consentVersion'=>$config['consent_version'],'items'=>[]],'127.0.0.'.$i,'isolated consent');
    concurrencyCheck($replay['orderNumber']===$result['orderNumber']&&$replay['createdAt']===$result['createdAt'],'replay stable for concurrent order '.$i);
}
sort($numbers);concurrencyCheck($numbers===range(1,$workers),'parallel allocation is unique and contiguous');
foreach (glob($root.'/result-*')?:[] as $resultFile) unlink($resultFile);
unset($app,$db);foreach ([$path,$path.'-journal',$path.'-wal',$path.'-shm'] as $file) if (is_file($file)) unlink($file);
if (!rmdir($root)) throw new RuntimeException('Could not remove isolated concurrency directory');
echo "Backend concurrency checks complete\n";
