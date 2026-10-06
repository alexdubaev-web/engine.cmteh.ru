<?php
// Engine deployment template only. Not an active configuration.
// Copy to backend/config.php outside public_html only after owner approval
// and verified infrastructure setup. Never upload this template as config.php.
return [
    'enabled' => false,
    'russian_infrastructure_confirmed' => false,
    'legal_documents_confirmed' => false,
    'origin' => 'https://engine.cmteh.ru',
    'operator_name' => 'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «СМ ТЕХНО»',
    'privacy_email' => 'info@cmteh.ru',
    'consent_version' => '2026-10-06',
    'key' => '', // Generate and store only in the protected config.php.
    'database' => [
        'dsn' => 'UNCONFIGURED — database has not been created or verified',
        'user' => 'UNCONFIGURED',
        'password' => '',
    ],
    'smtp' => [
        'host' => 'smtp.yandex.ru', 'port' => 465, 'encryption' => 'ssl',
        'username' => 'info@cmteh.ru', 'password' => '',
        'from' => 'info@cmteh.ru', 'from_name' => 'СМ ТЕХНО', 'to' => 'info@cmteh.ru',
    ],
    // Proposed technical setting only; owner approval and policy alignment required.
    'retention_days' => 90,
    'rate_limit' => 8,
    'immediate_delivery' => true,
];
