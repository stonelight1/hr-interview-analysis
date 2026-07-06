#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_ONLY=0
FRONTEND_ONLY=0
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

usage() {
    cat <<'EOF'
Usage: ./stop.sh [options]

Options:
  --backend-only           Stop only the FastAPI backend
  --frontend-only          Stop only the Vite frontend
  --backend-port PORT      Backend port, default: 8000
  --frontend-port PORT     Frontend port, default: 5173
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --backend-only)
            BACKEND_ONLY=1
            ;;
        --frontend-only)
            FRONTEND_ONLY=1
            ;;
        --backend-port)
            BACKEND_PORT="${2:?Missing value for --backend-port}"
            shift
            ;;
        --frontend-port)
            FRONTEND_PORT="${2:?Missing value for --frontend-port}"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [ "$BACKEND_ONLY" -eq 1 ] && [ "$FRONTEND_ONLY" -eq 1 ]; then
    echo "Use only one of --backend-only or --frontend-only." >&2
    exit 2
fi

kill_tree() {
    local pid="$1"
    local child

    for child in $(pgrep -P "$pid" 2>/dev/null || true); do
        kill_tree "$child"
    done

    kill "$pid" 2>/dev/null || true
}

stop_from_pid_file() {
    local name="$1"
    local pid_file="$2"
    local port="$3"
    shift 3
    local needles=("$@")

    echo "Stopping $name..."

    if [ ! -f "$pid_file" ]; then
        echo "  No pid file found."
        stop_by_port "$name" "$port" "${needles[@]}"
        return
    fi

    local pid
    pid="$(head -n 1 "$pid_file" || true)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill_tree "$pid"
        echo "  Stopped PID $pid."
    else
        echo "  No running process found for PID file."
    fi

    rm -f "$pid_file"
}

stop_by_port() {
    local name="$1"
    local port="$2"
    shift 2
    local needles=("$@")
    local pids=""
    local pid
    local command_line
    local needle
    local matched

    if command -v lsof >/dev/null 2>&1; then
        pids="$(lsof -t -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    fi

    [ -n "$pids" ] || return

    for pid in $pids; do
        command_line="$(ps -p "$pid" -o command= 2>/dev/null || true)"
        matched=0
        for needle in "${needles[@]}"; do
            case "$command_line" in
                *"$needle"*)
                    matched=1
                    break
                    ;;
            esac
        done

        if [ "$matched" -eq 1 ]; then
            kill_tree "$pid"
            echo "  Stopped process on port $port (PID $pid)."
        else
            echo "  Port $port is used by PID $pid, but it does not look like $name. Skipped."
        fi
    done
}

if [ "$FRONTEND_ONLY" -eq 0 ]; then
    stop_from_pid_file "backend" "$RUN_DIR/backend.pid" "$BACKEND_PORT" "uvicorn" "app.main:app"
fi

if [ "$BACKEND_ONLY" -eq 0 ]; then
    stop_from_pid_file "frontend" "$RUN_DIR/frontend.pid" "$FRONTEND_PORT" "vite" "npm"
fi

echo "Done."
