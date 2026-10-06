<?php
declare(strict_types=1);

/**
 * One-time, fail-closed provisioning for the verified REG.RU engine site.
 * Keep this script private; it contains no credentials and never prints them.
 */
const ENGINE_SITE = '/var/www/u2797422/data/www/engine.cmteh.ru';
const ENGINE_ACCOUNT_ROOT = '/var/www/u2797422/data';
const ENGINE_STAGING_TOOLS = ENGINE_ACCOUNT_ROOT . '/.engine-cmteh-backups/pre-setup-20261006T113726Z/staging-deploy/tools';
const ENGINE_SECRETS = ENGINE_ACCOUNT_ROOT . '/.engine-cmteh-secrets';
const ENGINE_KEY_BACKUP = ENGINE_ACCOUNT_ROOT . '/.engine-cmteh-key-backups/20261006/encryption-key';

function stopSafely(string $message): never
{
    fwrite(STDERR, "Setup stopped: {$message}\n");
    exit(1);
}

function rejectSymlink(string $path): void
{
    if (is_link($path)) stopSafely('unsafe path');
}

function ensurePrivateDirectory(string $path): void
{
    rejectSymlink($path);
    if (!is_dir($path) && !@mkdir($path, 0700)) stopSafely('cannot create protected directory');
    rejectSymlink($path);
    $real = realpath($path);
    if ($real !== $path || !is_dir($real) || !@chmod($real, 0700)) stopSafely('cannot protect directory');
}

function ensurePrivateBackupDirectory(): void
{
    $root = ENGINE_ACCOUNT_ROOT . '/.engine-cmteh-key-backups';
    ensurePrivateDirectory($root);
    ensurePrivateDirectory($root . '/20261006');
}

function readSecret(string $path, bool $key = false): string
{
    rejectSymlink($path);
    if (!file_exists($path)) return '';
    if (!is_file($path) || !is_readable($path)) stopSafely('invalid secret file');
    $stat = @stat($path);
    if (!is_array($stat) || !isset($stat['mode'], $stat['uid'])
        || (($stat['mode'] & 0777) !== 0600) || (function_exists('posix_geteuid') && $stat['uid'] !== posix_geteuid())) {
        stopSafely('invalid secret file');
    }
    $bytes = @file_get_contents($path);
    if (!is_string($bytes)) stopSafely('invalid secret file');
    if ($key) {
        $candidate = str_ends_with($bytes, "\n") ? substr($bytes, 0, -1) : $bytes;
        if (!preg_match('/^[a-f0-9]{64}$/D', $candidate)) stopSafely('invalid secret file');
        return $candidate;
    }
    if ($bytes === '') stopSafely('invalid secret file');
    return $bytes;
}

function exclusiveWrite(string $path, string $bytes, int $mode): array
{
    rejectSymlink($path);
    $handle = @fopen($path, 'x+b');
    if ($handle === false) stopSafely('target already exists or cannot be created');
    $opened = fstat($handle);
    $length = strlen($bytes);
    $written = 0;
    while ($written < $length) {
        $n = fwrite($handle, substr($bytes, $written));
        if ($n === false || $n === 0) {
            fclose($handle);
            stopSafely('cannot write protected file');
        }
        $written += $n;
    }
    $ok = fflush($handle) && @chmod($path, $mode);
    fclose($handle);
    if (!$ok) stopSafely('cannot protect file');
    return $opened;
}

function unlinkIfOwned(string $path, array $opened): void
{
    $current = @lstat($path);
    if (is_array($current) && isset($current['dev'], $current['ino'], $opened['dev'], $opened['ino'])
        && $current['dev'] === $opened['dev'] && $current['ino'] === $opened['ino']) {
        @unlink($path);
    }
}

if (PHP_SAPI !== 'cli' || PHP_VERSION_ID < 80300 || !extension_loaded('sodium') || !extension_loaded('pdo_mysql')) {
    stopSafely('requires PHP CLI 8.3+, sodium and pdo_mysql');
}
if (realpath(__DIR__) !== ENGINE_STAGING_TOOLS || realpath(ENGINE_ACCOUNT_ROOT) !== ENGINE_ACCOUNT_ROOT
    || realpath(ENGINE_SITE) !== ENGINE_SITE || realpath(ENGINE_SITE . '/public_html') !== ENGINE_SITE . '/public_html'
    || realpath(ENGINE_SITE . '/backend') !== ENGINE_SITE . '/backend') {
    stopSafely('site path does not match the verified engine domain');
}
$siteStat = @stat(ENGINE_SITE);
if (!is_array($siteStat) || !isset($siteStat['uid']) || !function_exists('posix_geteuid') || posix_geteuid() !== $siteStat['uid']) {
    stopSafely('run as the owner of the engine site files');
}
if (is_file(ENGINE_SITE . '/public_html/index.html') === false || !is_dir(ENGINE_SITE . '/backend')) {
    stopSafely('expected engine site files are missing');
}
$backend = ENGINE_SITE . '/backend';
$configPath = $backend . '/config.php';
rejectSymlink($backend);
rejectSymlink($configPath);
if (file_exists($configPath)) stopSafely('active configuration already exists');

umask(0077);
ensurePrivateDirectory(ENGINE_SECRETS);
ensurePrivateBackupDirectory();
$inputHelper = __DIR__ . '/engine-input-password.sh';
rejectSymlink($inputHelper);
if (!is_file($inputHelper) || !is_readable($inputHelper)) stopSafely('password helper is missing');
$helperContents = @file_get_contents($inputHelper);
if (!is_string($helperContents) || !str_starts_with($helperContents, "#!/usr/bin/env bash\n")) {
    stopSafely('password helper is invalid');
}
$installedHelper = ENGINE_SECRETS . '/input-password.sh';
rejectSymlink($installedHelper);
if (file_exists($installedHelper)) {
    $installedContents = @file_get_contents($installedHelper);
    if (!is_string($installedContents) || !hash_equals(hash('sha256', $helperContents), hash('sha256', $installedContents))) {
        stopSafely('installed password helper differs from the reviewed helper');
    }
    if (!@chmod($installedHelper, 0700)) stopSafely('cannot protect password helper');
} else {
    exclusiveWrite($installedHelper, $helperContents, 0700);
}
$keyPath = ENGINE_SECRETS . '/encryption-key';
$dbPath = ENGINE_SECRETS . '/db-password';
$smtpPath = ENGINE_SECRETS . '/smtp-password';
$key = readSecret($keyPath, true);
// Validate any already supplied passwords without retaining or printing them.
readSecret($dbPath);
readSecret($smtpPath);

if ($key === '') {
    if (file_exists(ENGINE_KEY_BACKUP)) {
        $key = readSecret(ENGINE_KEY_BACKUP, true);
    } else {
        $key = bin2hex(random_bytes(32));
    }
    // Exclusive creation ensures a concurrent owner-created key is never overwritten.
    exclusiveWrite($keyPath, $key . "\n", 0600);
}
if (!file_exists(ENGINE_KEY_BACKUP)) {
    exclusiveWrite(ENGINE_KEY_BACKUP, $key . "\n", 0600);
} else {
    $backup = readSecret(ENGINE_KEY_BACKUP, true);
    if (!hash_equals($key, $backup)) stopSafely('protected key backup does not match');
}
$config = [
    'enabled' => false,
    'russian_infrastructure_confirmed' => false,
    'legal_documents_confirmed' => false,
    'origin' => 'https://engine.cmteh.ru',
    'operator_name' => 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «СМ ТЕХНО»',
    'privacy_email' => 'info@cmteh.ru',
    'consent_version' => '2026-10-06',
    'key' => "",
    'database' => [
        'dsn' => 'mysql:host=localhost;dbname=u2797422_engine_orders;charset=utf8mb4',
        'user' => 'u2797422_engine_orders',
        'password' => '',
    ],
    'smtp' => [
        'host' => 'smtp.yandex.ru', 'port' => 465, 'encryption' => 'ssl',
        'username' => 'info@cmteh.ru', 'password' => '',
        'from' => 'info@cmteh.ru', 'from_name' => 'СМ ТЕХНО', 'to' => 'info@cmteh.ru',
    ],
    'retention_days' => 90,
    'rate_limit' => 8,
    'immediate_delivery' => false,
];
$config['key'] = null;
$config['database']['password'] = null;
$config['smtp']['password'] = null;
$source = "<?php\ndeclare(strict_types=1);\n// Generated by tools/prepare_engine_config.php; secret values stay in protected files.\n"
    . '$readProtectedSecret = static function (string $path, bool $key = false): string {' . "\n"
    . '    $secretDirectory = ' . var_export(ENGINE_SECRETS, true) . ';' . "\n"
    . '    $expectedOwnerUid = ' . (string) $siteStat['uid'] . ';' . "\n"
    . '    if ($path !== $secretDirectory . "/encryption-key" && $path !== $secretDirectory . "/db-password" && $path !== $secretDirectory . "/smtp-password") throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    if (is_link($secretDirectory) || realpath($secretDirectory) !== $secretDirectory || is_link($path)) throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    $directoryStat = @stat($secretDirectory);' . "\n"
    . '    if (!is_array($directoryStat) || !is_dir($secretDirectory) || (($directoryStat["mode"] & 0777) !== 0700) || $directoryStat["uid"] !== $expectedOwnerUid) throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    if (!file_exists($path)) { if ($key) throw new RuntimeException("Protected configuration is unavailable"); return ""; }' . "\n"
    . '    $stat = @stat($path);' . "\n"
    . '    if (!is_array($stat) || !is_file($path) || !is_readable($path) || (($stat["mode"] & 0777) !== 0600) || $stat["uid"] !== $expectedOwnerUid) throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    $bytes = @file_get_contents($path);' . "\n"
    . '    if (!is_string($bytes) || $bytes === "") throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    if ($key) {' . "\n"
    . '        $bytes = str_ends_with($bytes, "\\n") ? substr($bytes, 0, -1) : $bytes;' . "\n"
    . '        if (!preg_match("/^[a-f0-9]{64}$/D", $bytes)) throw new RuntimeException("Protected configuration is unavailable");' . "\n"
    . '    }' . "\n"
    . '    return $bytes;' . "\n"
    . '};' . "\n"
    . '$config = ' . var_export($config, true) . ";\n"
    . '$config["key"] = $readProtectedSecret(' . var_export($keyPath, true) . ', true);' . "\n"
    . '$config["database"]["password"] = $readProtectedSecret(' . var_export($dbPath, true) . ');' . "\n"
    . '$config["smtp"]["password"] = $readProtectedSecret(' . var_export($smtpPath, true) . ');' . "\n"
    . 'return $config;' . "\n";
$temporary = $backend . '/.config.php.' . bin2hex(random_bytes(8)) . '.tmp';
$temporaryInode = exclusiveWrite($temporary, $source, 0600);
// Hard-link publication is atomic and fails if config.php appeared after our earlier check.
if (!@link($temporary, $configPath)) {
    unlinkIfOwned($temporary, $temporaryInode);
    stopSafely('configuration target exists or cannot be published');
}
unlinkIfOwned($temporary, $temporaryInode);
@chmod($configPath, 0600);
echo "Private configuration prepared with all intake gates disabled.\n";
