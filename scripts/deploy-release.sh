#!/usr/bin/env bash
# Deploys a released tag to the production host through the SSM document that
# open-projects-hub-infra manages. Run it from your machine with credentials for the AWS
# account that holds the host (the account's SCPs forbid the GitHub OIDC provider, so CI cannot).
#   AWS_PROFILE=ophub-new API_URL=https://api-oph.alonsovndev.com scripts/deploy-release.sh v0.1.0
set -euo pipefail

tag=${1:?Usage: scripts/deploy-release.sh vX.Y.Z}
if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Expected a vX.Y.Z tag, got $tag." >&2
  exit 1
fi

document=${SSM_DOCUMENT:-ophub-prod-deploy}
region=${AWS_REGION:-us-east-2}

instance_id=$(aws ec2 describe-instances --region "$region" \
  --filters "Name=tag:Name,Values=ophub-prod-api" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
if [ -z "$instance_id" ] || [ "$instance_id" = None ]; then
  echo "No running ophub-prod-api instance in $region for the current AWS credentials." >&2
  exit 1
fi
echo "Deploying $tag to $instance_id ($region)"

command_id=$(aws ssm send-command --region "$region" \
  --document-name "$document" \
  --targets "Key=instanceids,Values=$instance_id" \
  --parameters "tag=$tag" \
  --query Command.CommandId --output text)

status=Pending
for attempt in $(seq 1 120); do
  if ! status=$(aws ssm get-command-invocation --region "$region" --command-id "$command_id" \
    --instance-id "$instance_id" --query Status --output text 2>&1); then
    # The invocation record appears a moment after send-command; anything else is a real error.
    case "$status" in
      *InvocationDoesNotExist*) status=Pending ;;
      *) echo "$status" >&2; exit 1 ;;
    esac
  fi
  case "$status" in Success|Failed|Cancelled|TimedOut) break ;; esac
  sleep 5
done

aws ssm get-command-invocation --region "$region" --command-id "$command_id" \
  --instance-id "$instance_id" --query StandardOutputContent --output text
aws ssm get-command-invocation --region "$region" --command-id "$command_id" \
  --instance-id "$instance_id" --query StandardErrorContent --output text >&2

echo "SSM command status: $status"
[ "$status" = Success ] || exit 1

# The host check only proves the API answers locally. This proves Cloudflare reaches Caddy and
# /v1/* is routed to the API: an API error is JSON, while Caddy's 404 and Cloudflare 52x pages are not.
if [ -n "${API_URL:-}" ]; then
  for attempt in $(seq 1 12); do
    result=$(curl -sS -o /dev/null -w '%{http_code} %{content_type}' "$API_URL/v1/users/me/profile" || true)
    echo "GET /v1/users/me/profile -> $result"
    case "$result" in
      4??" application/json"*) exit 0 ;;
    esac
    sleep 5
  done
  echo "Expected a JSON 4xx from the API (unauthenticated request)." >&2
  exit 1
fi
