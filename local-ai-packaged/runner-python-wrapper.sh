#!/bin/sh
set -eu

echo "[runner-python-wrapper] starting python runner"
echo "[runner-python-wrapper] N8N_RUNNERS_EXTERNAL_ALLOW=${N8N_RUNNERS_EXTERNAL_ALLOW:-}"
echo "[runner-python-wrapper] N8N_BLOCK_ENV_ACCESS_IN_NODE=${N8N_BLOCK_ENV_ACCESS_IN_NODE:-}"
echo "[runner-python-wrapper] YTA_PROXY_USERNAME=${YTA_PROXY_USERNAME:-}"
if [ -n "${YTA_PROXY_PASSWORD:-}" ]; then
  echo "[runner-python-wrapper] YTA_PROXY_PASSWORD_SET=true"
else
  echo "[runner-python-wrapper] YTA_PROXY_PASSWORD_SET=false"
fi

exec /opt/runners/task-runner-python/.venv/bin/python "$@"
