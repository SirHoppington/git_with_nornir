#!/bin/bash
set -euo pipefail

: "${OWNER:?set OWNER}"
: "${REPO:?set REPO}"
: "${ACCESS_TOKEN:?set ACCESS_TOKEN}"

REG_TOKEN=$(curl -fsSX POST \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${OWNER}/${REPO}/actions/runners/registration-token" \
    | jq -r .token)

./config.sh --unattended --replace \
    --url "https://github.com/${OWNER}/${REPO}" \
    --token "${REG_TOKEN}" \
    --name "$(hostname)" \
    --labels self-hosted \
    --work _work

cleanup() {
    echo "Removing runner..."
    ./config.sh remove --unattended --token "${REG_TOKEN}" || true
}
trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!
