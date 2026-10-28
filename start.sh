#!/bin/sh
set -eu

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

python -m app.monitor &
MONITOR_PID=$!

shutdown() {
    echo "Stopping Docker Health Monitor..."

    kill -TERM "$API_PID" "$MONITOR_PID" 2>/dev/null || true

    wait "$API_PID" 2>/dev/null || true
    wait "$MONITOR_PID" 2>/dev/null || true
}

trap shutdown TERM INT

while kill -0 "$API_PID" 2>/dev/null &&
      kill -0 "$MONITOR_PID" 2>/dev/null; do
    sleep 1
done

echo "API or monitor process stopped; shutting down."
shutdown
