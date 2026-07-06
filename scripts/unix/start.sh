#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_ONLY=0
FRONTEND_ONLY=0
NO_INSTALL=0
HOST_ADDRESS="${HOST_ADDRESS:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

usage() {
    cat <<'EOF'
Usage: ./start.sh [options]

Options:
  --backend-only           Start only the FastAPI backend
  --frontend-only          Start only the Vite frontend
  --no-install             Skip dependency installation
  --host HOST              Bind host, default: 127.0.0.1
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
        --no-install)
            NO_INSTALL=1
            ;;
        --host)
            HOST_ADDRESS="${2:?Missing value for --host}"
            shift
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

mkdir -p "$RUN_DIR"

require_cmd() {
    local name="$1"
    local hint="$2"
    if ! command -v "$name" >/dev/null 2>&1; then
        echo "Command '$name' was not found. $hint" >&2
        exit 1
    fi
}

pid_alive() {
    local pid_file="$1"
    [ -f "$pid_file" ] || return 1

    local pid
    pid="$(head -n 1 "$pid_file" || true)"
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        rm -f "$pid_file"
        return 1
    fi

    return 0
}

port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
    elif command -v ss >/dev/null 2>&1; then
        ss -ltn "( sport = :$port )" | grep -q ":$port"
    elif command -v netstat >/dev/null 2>&1; then
        netstat -an | grep -E "[.:]$port[[:space:]].*LISTEN" >/dev/null 2>&1
    else
        return 1
    fi
}

assert_port_free() {
    local service="$1"
    local port="$2"
    if port_in_use "$port"; then
        echo "$service port $port is already in use. Run ./scripts/unix/stop.sh first or choose another port." >&2
        exit 1
    fi
}

wait_port() {
    local name="$1"
    local host="$2"
    local port="$3"
    local timeout="${4:-45}"
    local deadline=$((SECONDS + timeout))

    if [ "$host" = "0.0.0.0" ]; then
        host="127.0.0.1"
    fi

    while [ "$SECONDS" -lt "$deadline" ]; do
        if (echo >"/dev/tcp/$host/$port") >/dev/null 2>&1; then
            echo "  $name is listening on http://localhost:$port"
            return 0
        fi
        sleep 1
    done

    echo "$name did not start within $timeout seconds. Check logs in $RUN_DIR." >&2
    exit 1
}

ensure_backend_env() {
    if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        echo "  Created backend/.env from backend/.env.example. Set DEEPSEEK_API_KEY before using AI features."
    fi
}

start_backend() {
    local pid_file="$RUN_DIR/backend.pid"
    local log_file="$RUN_DIR/backend.log"
    local err_file="$RUN_DIR/backend.err.log"
    local python_bin="$BACKEND_DIR/.venv/bin/python"

    if pid_alive "$pid_file"; then
        echo "Backend already appears to be running (PID $(cat "$pid_file"))."
        return
    fi

    assert_port_free "Backend" "$BACKEND_PORT"
    require_cmd "uv" "Install uv first: https://docs.astral.sh/uv/"

    echo ""
    echo "[1/4] Preparing backend virtual environment"
    if [ ! -x "$python_bin" ]; then
        (cd "$BACKEND_DIR" && uv venv)
    fi

    if [ ! -x "$python_bin" ]; then
        echo "Backend virtual environment was not created at $BACKEND_DIR/.venv." >&2
        exit 1
    fi

    ensure_backend_env

    if [ "$NO_INSTALL" -eq 0 ]; then
        echo ""
        echo "[2/4] Installing backend dependencies"
        (cd "$BACKEND_DIR" && uv pip install --python "$python_bin" -r requirements.txt)
    else
        echo ""
        echo "[2/4] Skipping backend dependency install (--no-install)"
    fi

    echo ""
    echo "[3/4] Starting backend on port $BACKEND_PORT"
    (
        cd "$BACKEND_DIR"
        nohup "$python_bin" -m uvicorn app.main:app --reload --host "$HOST_ADDRESS" --port "$BACKEND_PORT" \
            >"$log_file" 2>"$err_file" &
        echo "$!" >"$pid_file"
    )
    wait_port "Backend" "$HOST_ADDRESS" "$BACKEND_PORT"
}

start_frontend() {
    local pid_file="$RUN_DIR/frontend.pid"
    local log_file="$RUN_DIR/frontend.log"
    local err_file="$RUN_DIR/frontend.err.log"

    if pid_alive "$pid_file"; then
        echo "Frontend already appears to be running (PID $(cat "$pid_file"))."
        return
    fi

    assert_port_free "Frontend" "$FRONTEND_PORT"
    require_cmd "npm" "Install Node.js/npm first."

    echo ""
    echo "[4/4] Preparing frontend"
    if [ "$NO_INSTALL" -eq 0 ] && [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
            (cd "$FRONTEND_DIR" && npm ci)
        else
            (cd "$FRONTEND_DIR" && npm install)
        fi
    elif [ "$NO_INSTALL" -eq 1 ]; then
        echo "  Skipping frontend dependency install (--no-install)"
    else
        echo "  node_modules already exists"
    fi

    echo "  Starting frontend on port $FRONTEND_PORT"
    (
        cd "$FRONTEND_DIR"
        nohup npm run dev -- --host "$HOST_ADDRESS" --port "$FRONTEND_PORT" \
            >"$log_file" 2>"$err_file" &
        echo "$!" >"$pid_file"
    )
    wait_port "Frontend" "$HOST_ADDRESS" "$FRONTEND_PORT"
}

echo "================================================"
echo " Starting HR Interview Analysis System"
echo "================================================"

if [ "$FRONTEND_ONLY" -eq 0 ]; then
    start_backend
fi

if [ "$BACKEND_ONLY" -eq 0 ]; then
    start_frontend
fi

echo ""
echo "================================================"
if [ "$FRONTEND_ONLY" -eq 0 ]; then
    echo " Backend:  http://localhost:$BACKEND_PORT"
fi
if [ "$BACKEND_ONLY" -eq 0 ]; then
    echo " Frontend: http://localhost:$FRONTEND_PORT"
fi
echo " Logs:     $RUN_DIR"
echo " Stop:     ./scripts/unix/stop.sh"
echo "================================================"
