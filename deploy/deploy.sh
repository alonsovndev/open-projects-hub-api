#!/bin/bash
# Deploys a release tag on the EC2 host. Runs as root via the SSM document ophub-prod-deploy.
set -euo pipefail
umask 077

tag="${1:?usage: deploy.sh vX.Y.Z}"
raw_url="https://raw.githubusercontent.com/alonsovndev/open-projects-hub-api/$tag/deploy"
ssm_prefix="/ophub/prod"
compose=(docker compose -f compose.prod.yml --env-file .env)

mkdir -p /opt/ophub
cd /opt/ophub

imds_token=$(curl -fsS -X PUT http://169.254.169.254/latest/api/token \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
region=$(curl -fsS -H "X-aws-ec2-metadata-token: $imds_token" \
  http://169.254.169.254/latest/meta-data/placement/region)

curl -fsSL "$raw_url/compose.prod.yml" -o compose.prod.yml.new
curl -fsSL "$raw_url/Caddyfile" -o Caddyfile.new

# "N/A" marks a parameter nobody has filled in. It must stay unset: sentry-sdk reads
# SENTRY_DSN from the environment and crashes on "N/A". Values are single-quoted so
# Compose keeps "$", "#" and quotes literally.
: > .env.new
aws ssm get-parameters-by-path --region "$region" --path "$ssm_prefix" --with-decryption \
  --query 'Parameters[].[Name,Value]' --output text |
  while IFS=$'\t' read -r name value; do
    case "$value" in
      "N/A") continue ;;
      *"'"*)
        echo "Parameter ${name##*/} contains a single quote, which .env cannot hold" >&2
        exit 1
        ;;
    esac
    printf "%s='%s'\n" "${name##*/}" "$value" >> .env.new
  done
printf 'IMAGE_TAG=%s\n' "$tag" >> .env.new

mv compose.prod.yml.new compose.prod.yml
mv Caddyfile.new Caddyfile
mv .env.new .env

"${compose[@]}" pull
if ! "${compose[@]}" up -d --remove-orphans; then
  echo "Stack failed to start" >&2
  "${compose[@]}" logs --tail 60 api >&2
  exit 1
fi
# A replaced bind-mounted Caddyfile is not seen by a running container, and admin is off
# (no reload), so recreate Caddy on every deploy. The blip is a second or two.
"${compose[@]}" up -d --force-recreate --no-deps caddy

# Migrations run inside the api container before it serves, so readiness covers them.
for attempt in $(seq 1 45); do
  if curl -fsS http://127.0.0.1:8080/health/ready > /dev/null; then
    echo "Deployed $tag"
    "${compose[@]}" ps
    exit 0
  fi
  sleep 2
done

echo "API did not become ready within 90s" >&2
"${compose[@]}" logs --tail 60 api >&2
exit 1
