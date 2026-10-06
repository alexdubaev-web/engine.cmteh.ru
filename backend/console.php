<?php
declare(strict_types=1);
if (PHP_SAPI!=='cli') { http_response_code(404); exit; }
require __DIR__.'/app.php';
$cmd=$argv[1] ?? 'help';
if ($cmd==='key:generate') { echo bin2hex(random_bytes(32)).PHP_EOL; exit; }
if ($cmd==='help') { echo "Commands: key:generate, migrate, check, mail:retry, purge, list, export ID ABSOLUTE_PATH, delete ID\n"; exit; }
try {
    if (!is_file(__DIR__.'/config.php')) throw new RuntimeException('Copy config.example.php to private config.php first');
    $c=require __DIR__.'/config.php'; $app=new Orders($c);
    switch ($cmd) {
        case 'migrate': $app->migrate(); echo "Database ready\n"; break;
        case 'check': echo 'Configuration gate: '.(Orders::configured($c)?'ready':'disabled').PHP_EOL; echo 'Database connected; orders: '.count($app->listing()).PHP_EOL; break;
        case 'mail:retry': if (!Orders::configured($c)) throw new RuntimeException('Configuration gate disabled'); echo json_encode($app->deliver([$app,'sendMail']),JSON_THROW_ON_ERROR).PHP_EOL; break;
        case 'purge': echo 'Deleted expired records: '.$app->purge().PHP_EOL; break;
        case 'list': echo json_encode($app->listing(),JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR).PHP_EOL; break;
        case 'delete': echo 'Deleted records: '.$app->delete($argv[2] ?? '').PHP_EOL; break;
        case 'export':
            $path=$argv[3] ?? ''; $parent=realpath(dirname($path)); $web=realpath(__DIR__.'/../public_html');
            if (!$parent || !str_starts_with($path,'/') || ($web && ($parent===$web || str_starts_with($parent,$web.'/')))) throw new RuntimeException('Export must be outside public_html');
            $content=json_encode($app->export($argv[2] ?? ''),JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT|JSON_THROW_ON_ERROR);
            $old=umask(0077); $f=fopen($path,'x'); umask($old); if (!$f) throw new RuntimeException('Cannot create export (existing files are not overwritten)'); fwrite($f,$content); fclose($f); echo "Export created\n"; break;
        default: throw new RuntimeException('Unknown command');
    }
} catch (Throwable $e) { fwrite(STDERR,"Operation failed. Check private configuration, database schema, extensions and file permissions.\n"); exit(1); }
