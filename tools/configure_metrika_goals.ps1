param(
    [Parameter(Mandatory=$true)][string]$EvidenceDir,
    [switch]$Apply
)

# Default is a read-only plan. Credentials are read only from the process environment.
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($env:YANDEX_OAUTH_TOKEN)) { throw 'YANDEX_OAUTH_TOKEN unavailable' }
$counterId = 113475902
$base = "https://api-metrika.yandex.net/management/v1/counter/$counterId"
$headers = @{Authorization = 'OAuth ' + $env:YANDEX_OAUTH_TOKEN}
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null

function Api([string]$method,[string]$url,$payload=$null) {
    $arguments=@{Uri=$url;Method=$method;Headers=$headers;TimeoutSec=40;SkipHttpErrorCheck=$true}
    if ($null -ne $payload) {
        $arguments.ContentType='application/json; charset=utf-8'
        $arguments.Body=[System.Text.Encoding]::UTF8.GetBytes(($payload | ConvertTo-Json -Depth 15 -Compress))
    }
    try { $response=Invoke-WebRequest @arguments }
    catch { throw 'Transport failure. No automatic write retry; inspect current goals before further action.' }
    $body=$null
    try { $body=$response.Content | ConvertFrom-Json } catch {}
    if ([int]$response.StatusCode -ne 200) {
        $code=[int]$response.StatusCode
        $safeErrors=@($body.errors | ForEach-Object {
            $message=[string]$_.message
            foreach ($envName in @('YANDEX_OAUTH_TOKEN','YANDEX_CLOUD_API_KEY','YANDEX_CLOUD_FOLDER_ID')) {
                $secret=[Environment]::GetEnvironmentVariable($envName)
                if (![string]::IsNullOrEmpty($secret)) {$message=$message.Replace($secret,'[REDACTED]')}
            }
            [ordered]@{type=$_.error_type;message=$message}
        })
        [ordered]@{http=$code;method=$method;errors=$safeErrors} | ConvertTo-Json -Depth 8 |
            Set-Content -LiteralPath (Join-Path $EvidenceDir 'api-error.json') -Encoding utf8
        throw "API HTTP $code. Sanitized validation details saved; request headers suppressed. No automatic write retry."
    }
    if ($null -eq $body) { throw 'API returned invalid JSON. No automatic write retry.' }
    return $body
}
function GoalKey($goal) {
    $conditions=@($goal.conditions | ForEach-Object {([string]$_.type)+':'+([string]$_.url)} | Sort-Object)
    return ([string]$goal.type)+'|'+($conditions -join '|')
}
function Snapshot($goals,[string]$name) {
    @($goals | Select-Object id,name,type,conditions,is_favorite,hide_phone_number) |
        ConvertTo-Json -Depth 15 -AsArray | Set-Content -LiteralPath (Join-Path $EvidenceDir $name) -Encoding utf8
}

$counter=(Api 'GET' $base).counter
if ($counter.id -ne $counterId -or $counter.site -ne 'engine.cmteh.ru' -or $counter.permission -ne 'own') {
    throw 'Unexpected counter, domain or owner permission; no writes performed.'
}
$contacts=Invoke-WebRequest -Uri 'https://engine.cmteh.ru/contacts/' -Method Get -TimeoutSec 30
$phones=@([regex]::Matches($contacts.Content,'href="tel:([^"?]+)"') | ForEach-Object {$_.Groups[1].Value} | Sort-Object -Unique)
$emails=@([regex]::Matches($contacts.Content,'href="mailto:([^"?]+)') | ForEach-Object {$_.Groups[1].Value} | Sort-Object -Unique)
if ($phones.Count -ne 4 -or $emails.Count -ne 2) { throw 'Contact inventory changed; review before applying.' }

$spec=@(
    @('form_success','Заявка принята сервером',$true),
    @('search','Поиск по каталогу',$false),
    @('search_empty','Диагностика: поиск без результатов',$false),
    @('add_to_cart','Товар добавлен в корзину',$false),
    @('cart_open','Открытие корзины',$false),
    @('form_start','Начало заполнения заявки',$false),
    @('form_error','Диагностика: ошибка заявки',$false)
)
$desired=@($spec | ForEach-Object {
    # Live API expects numeric 0/1 here despite its generated boolean schema.
    [ordered]@{name=$_[1];type='action';is_favorite=[int][bool]$_[2];conditions=@(@{type='exact';url=$_[0]})}
})
$desired += [ordered]@{name='Клик по номеру телефона';type='phone';is_favorite=0;hide_phone_number=0;conditions=@($phones | ForEach-Object {@{type='exact';url=$_}})}
$desired += [ordered]@{name='Клик по email';type='email';is_favorite=0;conditions=@($emails | ForEach-Object {@{type='exact';url=$_}})}
$desired | ConvertTo-Json -Depth 15 -AsArray | Set-Content -LiteralPath (Join-Path $EvidenceDir 'desired.json') -Encoding utf8
$before=@((Api 'GET' "$base/goals").goals)
Snapshot $before 'goals-before.json'
$current=$before
$results=@()
foreach ($goal in $desired) {
    $key=GoalKey $goal
    $existing=@($current | Where-Object {(GoalKey $_) -eq $key})
    if ($existing.Count -gt 1) { throw 'Duplicate matching goals already exist; no destructive cleanup performed.' }
    if ($existing.Count -eq 1) {
        $results += [ordered]@{key=$key;name=$existing[0].name;id=$existing[0].id;action='reused'}
    } elseif (!$Apply) {
        $results += [ordered]@{key=$key;name=$goal.name;action='would_create'}
    } else {
        $created=(Api 'POST' "$base/goals" @{goal=$goal}).goal
        if (!$created.id -or (GoalKey $created) -ne $key) { throw 'Unexpected creation response. Inspect current goals before any retry.' }
        $current += $created
        $results += [ordered]@{key=$key;name=$created.name;id=$created.id;action='created';http=200}
        $results | ConvertTo-Json -Depth 12 -AsArray | Set-Content -LiteralPath (Join-Path $EvidenceDir 'operations.json') -Encoding utf8
    }
}
if ($Apply) {
    $after=@((Api 'GET' "$base/goals").goals)
    Snapshot $after 'goals-after.json'
    foreach ($goal in $desired) {
        $matches=@($after | Where-Object {(GoalKey $_) -eq (GoalKey $goal)})
        if ($matches.Count -ne 1) { throw 'Final goal verification failed.' }
        if ($goal.name -eq 'Заявка принята сервером' -and !$matches[0].is_favorite) { throw 'Main goal is not favorite.' }
        if ($goal.type -eq 'phone' -and $matches[0].hide_phone_number) { throw 'Unexpected phone hiding setting.' }
    }
    foreach ($old in $before) {
        $retained=@($after | Where-Object {$_.id -eq $old.id})
        if ($retained.Count -ne 1 -or (GoalKey $retained[0]) -ne (GoalKey $old)) { throw 'Existing goal preservation check failed.' }
    }
}
$results | ConvertTo-Json -Depth 12 -AsArray | Set-Content -LiteralPath (Join-Path $EvidenceDir 'operations.json') -Encoding utf8
$results | ForEach-Object {[pscustomobject]@{name=$_.name;action=$_.action;id=$_.id}} | ConvertTo-Json -Compress
