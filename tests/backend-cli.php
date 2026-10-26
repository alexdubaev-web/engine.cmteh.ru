<?php
declare(strict_types=1);

function cliCheck(bool $ok,string $message): void { if (!$ok) throw new RuntimeException($message); echo "PASS $message\n"; }
function runConsole(string $script,string $command): array {
    $pipes=[];
    $process=proc_open([PHP_BINARY,$script,$command],[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes);
    if (!is_resource($process)) throw new RuntimeException('Could not start isolated console');
    fclose($pipes[0]);$stdout=stream_get_contents($pipes[1]);fclose($pipes[1]);$stderr=stream_get_contents($pipes[2]);fclose($pipes[2]);
    return ['code'=>proc_close($process),'stdout'=>$stdout,'stderr'=>$stderr];
}
function copyTree(string $source,string $target): void {
    if (!is_dir($target)) mkdir($target,0700,true);
    foreach (new DirectoryIterator($source) as $entry) {
        if ($entry->isDot()) continue;
        if ($entry->getFilename()==='config.php') continue;
        $from=$entry->getPathname();$to=$target.DIRECTORY_SEPARATOR.$entry->getFilename();
        if ($entry->isDir()) copyTree($from,$to); else copy($from,$to);
    }
}
$root=sys_get_temp_dir().'/engine-cli-'.bin2hex(random_bytes(8));$backend=$root.'/backend';$public=$root.'/public_html';
try {
    copyTree(__DIR__.'/../backend',$backend);mkdir($public.'/consent',0700,true);file_put_contents($public.'/consent/index.html','test consent');
    $dbPath=$root.'/orders.sqlite';$key=str_repeat('ab',32);
    $config="<?php return ".var_export([
        'enabled'=>true,'russian_infrastructure_confirmed'=>true,'legal_documents_confirmed'=>true,
        'origin'=>'https://engine.example.test','operator_name'=>'Test Operator','privacy_email'=>'privacy@example.test',
        'consent_version'=>'test','key'=>$key,'database'=>['dsn'=>'sqlite:'.$dbPath,'user'=>'','password'=>''],
        'smtp'=>['host'=>'smtp.invalid','port'=>465,'encryption'=>'ssl','username'=>'user','password'=>'test','from'=>'from@example.test','from_name'=>'Test','to'=>'to@example.test'],
        'retention_days'=>90,'rate_limit'=>8,'mail_alert_after_seconds'=>900,'immediate_delivery'=>false,
    ],true).";\n";
    file_put_contents($backend.'/config.php',$config);
    $script=$backend.'/console.php';$help=runConsole($script,'help');cliCheck(str_contains($help['stdout'],'mail:health'),'console help lists mail health command');
    $migrate=runConsole($script,'migrate');cliCheck($migrate['code']===0,'isolated console migration succeeds');
    $db=new PDO('sqlite:'.$dbPath);$insert=$db->prepare("INSERT INTO orders (id,fingerprint,created_at,payload,mail_status,attempts,next_attempt,lease,lease_until,order_number) VALUES (?,?,?,?,?,?,?,NULL,0,NULL)");$now=time();
    foreach ([['old-pending',$now-901,'pending',0],['many-retries',$now-10,'retry',5],['recent-pending',$now-1,'pending',0]] as [$id,$created,$state,$attempts]) $insert->execute([$id,'test',$created,'not-encrypted',$state,$attempts,$now-1]);
    $db=null;
    $health=runConsole($script,'mail:health');$report=json_decode($health['stdout'],true);
    cliCheck($health['code']===1&&is_array($report)&&($report['queued']??null)===3&&($report['failed']??null)===1&&($report['oldestAgeSeconds']??0)>=900&&($report['alert']??false)===true,'mail:health reports queue age and failed retries with nonzero alert exit');
    cliCheck(!preg_match('/not-encrypted|example\.test/',$health['stdout']),'mail:health output contains no payload or contact data');
    $retry=runConsole($script,'mail:retry');$retryReport=json_decode($retry['stdout'],true);
    cliCheck($retry['code']===1&&$retryReport['retry']===3,'mail:retry returns nonzero when delivery attempts fail');
} finally {
    if (is_dir($root)) {
        $iterator=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($root,FilesystemIterator::SKIP_DOTS),RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($iterator as $entry) $entry->isDir()?rmdir($entry->getPathname()):unlink($entry->getPathname());
        rmdir($root);
    }
}
echo "Backend CLI checks complete\n";
