<?php
// Copy to config.php OUTSIDE public_html. Never publish this file.
return [
    'enabled' => false,
    'russian_infrastructure_confirmed' => false, // hosting, database, backups and mail
    'legal_documents_confirmed' => false, // replace public policy/consent drafts first
    'origin' => 'https://example.ru',
    'operator_name' => '', // full legal name
    'privacy_email' => '',
    'consent_version' => '2026-10-04',
    'key' => '', // php backend/console.php key:generate; keep separate backup of key
    'database' => [
        'dsn' => 'mysql:host=localhost;dbname=cm_techno;charset=utf8mb4',
        'user' => '', 'password' => '',
        // SQLite also supported: sqlite:/absolute/private/path/orders.sqlite
    ],
    'smtp' => [
        'host' => '', 'port' => 465, 'encryption' => 'ssl', // ssl or tls only
        'username' => '', 'password' => '',
        'from' => '', 'from_name' => 'СМ ТЕХНО', 'to' => '',
    ],
    'retention_days' => 90, // set to the justified period in your documents
    'rate_limit' => 8, // accepted requests per IP per 15 minutes
    'immediate_delivery' => true,
];
