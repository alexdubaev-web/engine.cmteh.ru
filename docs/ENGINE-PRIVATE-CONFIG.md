# Private engine configuration preparation

This procedure is for the verified REG.RU site only: `/var/www/u2797422/data/www/engine.cmteh.ru` (account `u2797422`). It does not change the public site, order API, legal pages, catalog, database contents, DNS, or mail routing. Do not run it until the lead explicitly authorizes the remote preparation.

The private script `tools/prepare_engine_config.php` requires the site-owned PHP 8.3 CLI with `sodium` and `pdo_mysql`. It refuses a different site path, a different site-file owner, symlinks, unreadable/invalid secret files, or an existing `backend/config.php`. It creates `/var/www/u2797422/data/.engine-cmteh-secrets` with mode `0700`, keeps secret files at `0600`, and atomically publishes a `0600` config outside `public_html`. Intake flags stay false and immediate email delivery stays off.

The tool creates a random 32-byte encryption key only when neither a key nor its protected backup exists. It exclusively preserves `/var/www/u2797422/data/.engine-cmteh-key-backups/20261006/encryption-key`; it never rotates or overwrites that key. If the working key file is absent later, it restores the same key from that backup. Do not include the key or secret directory in ordinary site backups. Never delete the key while encrypted order data exists; loss of both copies makes that data unreadable.

The first run prepares the key backup, installs the small audited password helper, and atomically creates the private PHP config even when password files are absent. The config reads the key and passwords from the protected files at runtime. A missing password file produces an empty password without a warning, so the database can be connected and migrated before SMTP is configured. Existing password files are read byte-for-byte, with no trimming; an empty file is rejected. Create each password directly in the ISPmanager shell, without putting it in shell history, command arguments, output, or chat. Run this one-line command to enter the database password:

```bash
bash /var/www/u2797422/data/.engine-cmteh-secrets/input-password.sh db
```

Use `bash /var/www/u2797422/data/.engine-cmteh-secrets/input-password.sh smtp` for the Yandex 360 application password. The helper accepts only `db` or `smtp`, prompts with hidden input, preserves exact bytes, rejects empty input and existing files/symlinks, uses `umask 077` and exclusive file creation, and unsets the password before exit. Do not paste either password into chat or a command itself. If the helper reports that a password file already exists, stop; do not delete or overwrite it as a retry strategy.

After reviewing and explicitly authorizing the remote preparation, upload both scripts to the fixed private staging directory and run the PHP script as the site-file owner, for example:

```bash
/opt/php/8.3/bin/php /var/www/u2797422/data/.engine-cmteh-backups/pre-setup-20261006T113726Z/staging-deploy/tools/prepare_engine_config.php
```

The script accepts only that fixed staging directory and the verified site path; never run a CGI wrapper or expose either script through HTTP. Every run refuses to overwrite an existing config. After setup, enter passwords independently with the helper; database migration can proceed with SMTP unset. Then verify the config endpoint reports disabled, perform the migration only against the confirmed new engine database, and test SMTP separately. Do not enable order intake on the strength of this preparation alone.

If preparation stops, inspect only filenames, ownership and permissions; do not print config or secret contents. A partial secret file must not be overwritten automatically. Resolve it with the account owner while preserving any existing key and backup. For rollback before database migration, remove only the newly created config and temporary staging files after checking they are the exact engine paths. Keep the encryption key and protected backup. After any encrypted order data exists, never remove or rotate the key as rollback.
