<?php
declare(strict_types=1);
require __DIR__.'/../backend/export.php';
function exportCheck(bool $ok,string $message): void { if (!$ok) throw new RuntimeException($message); echo "PASS $message\n"; }
$dir=sys_get_temp_dir().DIRECTORY_SEPARATOR.'cm-export-'.bin2hex(random_bytes(8)); mkdir($dir,0700);
$path=$dir.DIRECTORY_SEPARATOR.'success.json';$chunks=[];
$open=static fn()=>fopen($path,'x');
$write=static function($stream,string $remaining)use(&$chunks): int { $part=substr($remaining,0,3);$chunks[]=$part;return fwrite($stream,$part); };
writeExportFile($path,'{"complete":true}',$open,$write);
exportCheck(file_get_contents($path)==='{"complete":true}','short writes are completed before export succeeds');
$failedPath=$dir.DIRECTORY_SEPARATOR.'failed.json';
try { writeExportFile($failedPath,'payload',static fn()=>fopen($failedPath,'x'),static fn()=>false); throw new RuntimeException('write failure was ignored'); }
catch (RuntimeException $e) { exportCheck(!file_exists($failedPath),'failed write removes incomplete export'); }
$closePath=$dir.DIRECTORY_SEPARATOR.'close-failed.json';
try { writeExportFile($closePath,'payload',static fn()=>fopen($closePath,'x'),null,static function($stream){fclose($stream);return false;}); throw new RuntimeException('close failure was ignored'); }
catch (RuntimeException $e) { exportCheck(!file_exists($closePath),'failed close removes incomplete export'); }
unlink($path);rmdir($dir);
echo "Backend export checks complete\n";
