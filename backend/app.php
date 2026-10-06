<?php
declare(strict_types=1);

final class ApiError extends RuntimeException {
    public function __construct(public int $status, string $message) { parent::__construct($message); }
}
final class Orders {
    private PDO $db;
    private array $catalog;
    private string $key;
    public function __construct(private array $config, ?PDO $db = null) {
        if (!extension_loaded('sodium')) throw new RuntimeException('PHP sodium required');
        if (!preg_match('/^[a-f0-9]{64}$/i', $config['key'] ?? '')) throw new RuntimeException('Configure encryption key');
        $this->key = hex2bin($config['key']);
        $this->db = $db ?? new PDO($config['database']['dsn'], $config['database']['user'] ?? '', $config['database']['password'] ?? '', [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        if ($this->db->getAttribute(PDO::ATTR_DRIVER_NAME) === 'sqlite') $this->db->exec('PRAGMA busy_timeout=5000');
        $this->catalog = [];
        foreach (json_decode(file_get_contents(__DIR__.'/catalog.json'), true, 512, JSON_THROW_ON_ERROR) as $p) $this->catalog[$p['id']] = $p;
    }
    public static function configured(array $c): bool {
        $s = $c['smtp'] ?? [];
        return ($c['enabled'] ?? false) === true && ($c['russian_infrastructure_confirmed'] ?? false) === true
            && ($c['legal_documents_confirmed'] ?? false) === true && !empty($c['operator_name'])
            && filter_var($c['privacy_email'] ?? '', FILTER_VALIDATE_EMAIL) !== false
            && preg_match('~^https://[a-zA-Z0-9.-]+(?::\d+)?$~D', $c['origin'] ?? '') === 1
            && preg_match('/^[a-f0-9]{64}$/iD', $c['key'] ?? '') === 1
            && !empty($c['database']['dsn']) && !empty($s['host']) && !empty($s['username']) && !empty($s['password'])
            && in_array($s['encryption'] ?? '', ['ssl','tls'], true)
            && filter_var($s['from'] ?? '', FILTER_VALIDATE_EMAIL) !== false
            && filter_var($s['to'] ?? '', FILTER_VALIDATE_EMAIL) !== false
            && is_file(__DIR__.'/../public_html/consent/index.html');
    }
    public function migrate(): void {
        $this->db->exec("CREATE TABLE IF NOT EXISTS orders (id VARCHAR(36) PRIMARY KEY, fingerprint VARCHAR(64) NOT NULL, created_at BIGINT NOT NULL, payload MEDIUMTEXT NOT NULL, mail_status VARCHAR(16) NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, next_attempt BIGINT NOT NULL, lease VARCHAR(64) NULL, lease_until BIGINT NOT NULL DEFAULT 0)");
        $this->db->exec("CREATE TABLE IF NOT EXISTS rate_limits (bucket VARCHAR(64) PRIMARY KEY, hits INTEGER NOT NULL, expires_at BIGINT NOT NULL)");
    }
    private function encrypt(array $data): string {
        $nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        return base64_encode($nonce.sodium_crypto_secretbox(json_encode($data, JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR), $nonce, $this->key));
    }
    private function decrypt(string $data): array {
        $raw = base64_decode($data, true);
        if ($raw === false || strlen($raw) < 40) throw new RuntimeException('Corrupt payload');
        $plain = sodium_crypto_secretbox_open(substr($raw,24), substr($raw,0,24), $this->key);
        if ($plain === false) throw new RuntimeException('Invalid encryption key');
        return json_decode($plain, true, 512, JSON_THROW_ON_ERROR);
    }
    public function accept(array $d, string $ip, string $consentHtml): array {
        $id = $d['requestId'] ?? '';
        if (!is_string($id) || !preg_match('/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/iD', $id)) throw new ApiError(400,'Некорректный номер заявки. Обновите страницу.');
        $id = strtolower($id);
        foreach (['name'=>100,'contact'=>160,'comment'=>5000,'website'=>200] as $field=>$max) {
            $v = $d[$field] ?? '';
            if (!is_string($v) || preg_match('/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/', $v) || preg_match_all('/./us',$v) > $max || !preg_match('//u',$v)) throw new ApiError(400,'Проверьте поля заявки.');
            $d[$field] = trim($v);
        }
        if ($d['website'] !== '') throw new ApiError(400,'Заявка не принята.');
        if (($d['consent'] ?? false) !== true || ($d['consentVersion'] ?? '') !== $this->config['consent_version']) throw new ApiError(400,'Подтвердите согласие на обработку данных.');
        if (preg_match_all('/./us',$d['name']) < 2 || preg_match('/[\r\n]/',$d['contact']) || !(filter_var($d['contact'], FILTER_VALIDATE_EMAIL) || (preg_match('/^[+0-9 ()-]{10,25}$/D',$d['contact']) && strlen(preg_replace('/\D/','',$d['contact'])) >= 10))) throw new ApiError(400,'Укажите имя и корректный телефон или email.');
        $items = $d['items'] ?? [];
        if (!is_array($items) || !array_is_list($items) || count($items)>count($this->catalog)) throw new ApiError(400,'Проверьте список товаров.');
        $clean = []; $seen = []; $total = 0;
        foreach ($items as $item) {
            if (!is_array($item) || !is_string($item['id'] ?? null) || !isset($this->catalog[$item['id']]) || isset($seen[$item['id']]) || !is_int($item['quantity'] ?? null) || $item['quantity']<1 || $item['quantity']>999) throw new ApiError(400,'Проверьте товары и количество.');
            $p = $this->catalog[$item['id']]; $q = $item['quantity']; $seen[$p['id']] = true;
            $clean[] = ['id'=>$p['id'],'sku'=>$p['sku'],'name'=>$p['name'],'brand'=>$p['brand'],'quantity'=>$q,'price'=>$p['price']]; $total += $p['price']*$q;
        }
        if (!$clean && preg_match_all('/./us',$d['comment'])<5) throw new ApiError(400,'Добавьте товары или опишите нужную деталь.');
        $core = ['name'=>$d['name'],'contact'=>$d['contact'],'comment'=>$d['comment'],'items'=>$clean,'total'=>$total,'consentVersion'=>$this->config['consent_version']];
        $fingerprint = hash_hmac('sha256',json_encode($core,JSON_UNESCAPED_UNICODE|JSON_THROW_ON_ERROR),$this->key);
        $this->db->beginTransaction();
        try {
            $q=$this->db->prepare('SELECT fingerprint FROM orders WHERE id=?'); $q->execute([$id]); $old=$q->fetchColumn();
            if ($old !== false) { if (!hash_equals($old,$fingerprint)) throw new ApiError(409,'Этот номер уже использован. Измените заявку и повторите отправку.'); $this->db->commit(); return ['ok'=>true,'requestId'=>$id,'message'=>'Заявка уже зарегистрирована.']; }
            $now=time(); $bucket=hash_hmac('sha256',$ip.'|'.intdiv($now,900),$this->key);
            $sql=$this->db->getAttribute(PDO::ATTR_DRIVER_NAME)==='mysql' ? 'INSERT INTO rate_limits (bucket,hits,expires_at) VALUES (?,1,?) ON DUPLICATE KEY UPDATE hits=hits+1' : 'INSERT INTO rate_limits (bucket,hits,expires_at) VALUES (?,1,?) ON CONFLICT(bucket) DO UPDATE SET hits=hits+1';
            $q=$this->db->prepare($sql); $q->execute([$bucket,$now+1800]);
            $q=$this->db->prepare('SELECT hits FROM rate_limits WHERE bucket=?'); $q->execute([$bucket]);
            if ((int)$q->fetchColumn()>($this->config['rate_limit'] ?? 8)) throw new ApiError(429,'Слишком много заявок. Попробуйте через 15 минут.');
            $core['consent']=['given'=>true,'at'=>gmdate('c',$now),'version'=>$this->config['consent_version'],'sha256'=>hash('sha256',$consentHtml),'document'=>$consentHtml];
            $q=$this->db->prepare("INSERT INTO orders (id,fingerprint,created_at,payload,mail_status,next_attempt) VALUES (?,?,?,?,'pending',?)");
            $q->execute([$id,$fingerprint,$now,$this->encrypt($core),$now]); $this->db->commit();
        } catch (Throwable $e) { if ($this->db->inTransaction()) $this->db->rollBack();
            // Concurrent retry of the same id: acknowledge only identical content.
            if ($e instanceof PDOException && in_array((string)$e->getCode(), ['23000','23505'],true)) {
                $q=$this->db->prepare('SELECT fingerprint FROM orders WHERE id=?'); $q->execute([$id]); $old=$q->fetchColumn();
                if (is_string($old) && hash_equals($old,$fingerprint)) return ['ok'=>true,'requestId'=>$id,'message'=>'Заявка уже зарегистрирована.'];
                throw new ApiError(409,'Этот номер уже использован другой заявкой.');
            } throw $e;
        }
        return ['ok'=>true,'requestId'=>$id,'message'=>'Заявка зарегистрирована. Мы ответим по указанному контакту.'];
    }
    public function deliver(callable $send, int $limit=20): array {
        $now=time(); $q=$this->db->prepare("SELECT id FROM orders WHERE mail_status IN ('pending','retry','sending') AND next_attempt<=? AND lease_until<? ORDER BY created_at LIMIT ".max(1,min(100,$limit))); $q->execute([$now,$now]); $ids=$q->fetchAll(PDO::FETCH_COLUMN); $sent=0; $failed=0;
        foreach ($ids as $id) {
            $lease=bin2hex(random_bytes(16)); $q=$this->db->prepare("UPDATE orders SET mail_status='sending',lease=?,lease_until=? WHERE id=? AND mail_status IN ('pending','retry','sending') AND lease_until<?"); $q->execute([$lease,time()+300,$id,time()]); if (!$q->rowCount()) continue;
            $q=$this->db->prepare('SELECT * FROM orders WHERE id=? AND lease=?'); $q->execute([$id,$lease]); $row=$q->fetch(PDO::FETCH_ASSOC);
            try { $send($id,$this->decrypt($row['payload'])); $state='sent'; $sent++; }
            catch (Throwable $e) { $state='retry'; $failed++; /* Never log SMTP credentials or customer data. */ }
            $attempts=(int)$row['attempts']+1; $delay=min(86400,60*(2**min($attempts,10)));
            $q=$this->db->prepare('UPDATE orders SET mail_status=?,attempts=?,next_attempt=?,lease=NULL,lease_until=0 WHERE id=? AND lease=?'); $q->execute([$state,$attempts,time()+$delay,$id,$lease]);
        }
        return ['sent'=>$sent,'retry'=>$failed];
    }
    public function sendMail(string $id, array $data): void {
        foreach (['Exception','PHPMailer','SMTP'] as $f) require_once __DIR__.'/vendor/PHPMailer/'.$f.'.php';
        $s=$this->config['smtp']; $m=new PHPMailer\PHPMailer\PHPMailer(true);
        $m->isSMTP(); $m->Host=$s['host']; $m->Port=(int)$s['port']; $m->SMTPAuth=true; $m->Username=$s['username']; $m->Password=$s['password']; $m->SMTPSecure=$s['encryption']; $m->Timeout=5; $m->getSMTPInstance()->Timelimit=10;
        $m->CharSet='UTF-8'; $m->setFrom($s['from'],$s['from_name']); $m->addAddress($s['to']);
        if (filter_var($data['contact'],FILTER_VALIDATE_EMAIL)) $m->addReplyTo($data['contact']);
        $m->Subject='СМ ТЕХНО — заявка '.$id; $m->MessageID='<'.$id.'@'.parse_url($this->config['origin'],PHP_URL_HOST).'>';
        $lines=['Заявка: '.$id,'Имя: '.$data['name'],'Контакт: '.$data['contact'],'Комментарий: '.$data['comment'],''];
        foreach ($data['items'] as $p) $lines[]=$p['sku'].' | '.$p['brand'].' | '.$p['name'].' | '.$p['quantity'].' шт. | '.$p['price'].' ₽ / шт.';
        $lines[]='Итого по каталогу: '.$data['total'].' ₽. Цена, наличие и доставка требуют подтверждения.';
        $lines[]='Согласие: '.$data['consent']['version'].', '.$data['consent']['at']; $m->Body=implode("\n",$lines); $m->send();
    }
    public function purge(): int {
        $cutoff=time()-max(1,(int)$this->config['retention_days'])*86400;
        $q=$this->db->prepare('DELETE FROM orders WHERE created_at<? AND lease_until<?'); $q->execute([$cutoff,time()]); $count=$q->rowCount();
        $q=$this->db->prepare('DELETE FROM rate_limits WHERE expires_at<?'); $q->execute([time()]); return $count;
    }
    public function listing(): array { return $this->db->query('SELECT id,created_at,mail_status,attempts FROM orders ORDER BY created_at DESC LIMIT 100')->fetchAll(PDO::FETCH_ASSOC); }
    public function delete(string $id): int { $q=$this->db->prepare('DELETE FROM orders WHERE id=? AND lease_until<?'); $q->execute([$id,time()]); return $q->rowCount(); }
    public function export(string $id): array { $q=$this->db->prepare('SELECT payload FROM orders WHERE id=?'); $q->execute([$id]); $value=$q->fetchColumn(); if ($value===false) throw new RuntimeException('Order not found'); return $this->decrypt($value); }
}
