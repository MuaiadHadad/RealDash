#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -d "${ROOT_DIR}/.venv" ]]; then
    # shellcheck source=/dev/null
    source "${ROOT_DIR}/.venv/bin/activate"
fi

PYTHON_BIN="${PYTHON_BIN:-python}"
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-DjangoProject.settings}"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
export CHANNEL_LAYER_BACKEND="${CHANNEL_LAYER_BACKEND:-redis}"
export CELERY_TIMEZONE="${CELERY_TIMEZONE:-America/Sao_Paulo}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://127.0.0.1:6379/0}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://127.0.0.1:6379/1}"

function ensure_dependency() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "[run_dashboard] Missing dependency '$1'. Install it or adjust the script." >&2
        exit 1
    fi
}

if [[ "${CHANNEL_LAYER_BACKEND}" != "memory" ]]; then
    ensure_dependency redis-server
fi

ensure_dependency "${PYTHON_BIN}"
ensure_dependency celery

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
    "${PYTHON_BIN}" manage.py migrate --noinput
fi

pids=()
function stop_services() {
    if [[ ${#pids[@]} -gt 0 ]]; then
        echo "[run_dashboard] Stopping background services..."
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" >/dev/null 2>&1; then
                kill "$pid" || true
            fi
        done
        wait || true
    fi
}
trap stop_services EXIT INT TERM

if [[ "${CHANNEL_LAYER_BACKEND}" != "memory" ]] && [[ "${SKIP_REDIS_LAUNCH:-0}" != "1" ]]; then
    echo "[run_dashboard] Launching redis-server..."
    redis-server --save "" --appendonly no &
    pids+=($!)
    sleep 1
fi

echo "[run_dashboard] Starting Celery worker..."
celery -A DjangoProject worker --loglevel=info &
pids+=($!)

echo "[run_dashboard] Starting Celery beat..."
celery -A DjangoProject beat --loglevel=info &
pids+=($!)

if [[ "${ENABLE_STREAM_BRIDGES:-0}" == "1" ]]; then
    echo "[run_dashboard] Starting stream bridges..."
    "${PYTHON_BIN}" manage.py start_stream_bridges &
    pids+=($!)
fi

echo "[run_dashboard] Running Django development server (Ctrl+C to stop)..."
"${PYTHON_BIN}" manage.py runserver 0.0.0.0:8000
