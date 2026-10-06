<?php
declare(strict_types=1);

function writeExportFile(string $path,string $content,?callable $open=null,?callable $write=null,?callable $close=null): void {
    $open ??= static fn(string $path,string $mode)=>@fopen($path,$mode);
    $write ??= static fn($stream,string $bytes)=>@fwrite($stream,$bytes);
    $close ??= static fn($stream)=>@fclose($stream);
    $stream=$open($path,'x');
    if ($stream===false) throw new RuntimeException('Cannot create export (existing files are not overwritten)');
    $closed=false;$closeAttempted=false;
    try {
        $length=strlen($content);$offset=0;
        while ($offset<$length) {
            $written=$write($stream,substr($content,$offset));
            if (!is_int($written) || $written<=0) throw new RuntimeException('Incomplete export write');
            $offset += $written;
        }
        $closeAttempted=true;
        if (!$close($stream)) throw new RuntimeException('Cannot close export');
        $closed=true;
    } catch (Throwable $e) {
        try { if (!$closed && !$closeAttempted) $close($stream); } catch (Throwable) {}
        finally { @unlink($path); }
        throw $e;
    }
}
