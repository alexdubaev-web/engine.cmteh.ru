#!/usr/bin/env bash
set +x
umask 077
set -o noclobber

case "${1-}" in
  db) target='/var/www/u2797422/data/.engine-cmteh-secrets/db-password'; prompt='MySQL password: ' ;;
  smtp) target='/var/www/u2797422/data/.engine-cmteh-secrets/smtp-password'; prompt='Yandex app password: ' ;;
  *) printf 'Usage: engine-input-password.sh db|smtp\n' >&2; exit 2 ;;
esac

secret_dir='/var/www/u2797422/data/.engine-cmteh-secrets'
script_path='/var/www/u2797422/data/.engine-cmteh-secrets/input-password.sh'
if [[ "$secret_dir" != '/var/www/u2797422/data/.engine-cmteh-secrets' \
   || "$target" != "$secret_dir/db-password" && "$target" != "$secret_dir/smtp-password" \
   || -L "$secret_dir" || ! -d "$secret_dir" || -L "$target" || -e "$target" \
   || "$(readlink -f -- "$secret_dir" 2>/dev/null)" != "$secret_dir" \
   || "$(stat -c '%a:%u' -- "$secret_dir" 2>/dev/null)" != "700:$(id -u)" \
   || "$(readlink -f -- "${BASH_SOURCE[0]}" 2>/dev/null)" != "$script_path" \
   || "$(stat -c '%a:%u' -- "$script_path" 2>/dev/null)" != "700:$(id -u)" ]]; then
  printf 'Password file already exists or the protected directory is unavailable.\n' >&2
  exit 1
fi

IFS= read -r -s -p "$prompt" ENGINE_INPUT_PASSWORD || {
  printf '\nPassword input failed.\n' >&2
  unset ENGINE_INPUT_PASSWORD
  exit 1
}
printf '\n'
if [[ -z "$ENGINE_INPUT_PASSWORD" ]]; then
  printf 'Password cannot be empty.\n' >&2
  unset ENGINE_INPUT_PASSWORD
  exit 1
fi

if ! exec 3>"$target"; then
  printf 'Password file already exists or cannot be created.\n' >&2
  unset ENGINE_INPUT_PASSWORD
  exit 1
fi
if ! printf '%s' "$ENGINE_INPUT_PASSWORD" >&3; then
  exec 3>&-
  unset ENGINE_INPUT_PASSWORD
  printf 'Could not save password; a protected partial file may remain.\n' >&2
  exit 1
fi
exec 3>&-
unset ENGINE_INPUT_PASSWORD
printf 'Password saved in the protected file.\n'
