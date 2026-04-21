#!/bin/bash
APP_NAME="pysys-backend"
APP_DIR="/www/wwwroot/${APP_NAME}"
PYTHON="/www/server/panel/pyenv/bin/python3"
PID_FILE="${APP_DIR}/backend.pid"
LOG_FILE="${APP_DIR}/logs/uvicorn.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "${APP_NAME} is already running (PID: ${PID})"
            return 1
        fi
    fi

    cd "${APP_DIR}/backend"
    nohup ${PYTHON} -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 >> "${LOG_FILE}" 2>&1 &
    echo $! > "$PID_FILE"
    echo "${APP_NAME} started (PID: $(cat ${PID_FILE}))"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "${APP_NAME} stopped"
    else
        echo "${APP_NAME} is not running"
    fi
}

restart() {
    stop
    sleep 2
    start
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "${APP_NAME} is running (PID: ${PID})"
            return 0
        fi
    fi
    echo "${APP_NAME} is not running"
    return 1
}

case "$1" in
    start)   start   ;;
    stop)    stop    ;;
    restart) restart ;;
    status)  status  ;;
    *)       echo "Usage: $0 {start|stop|restart|status}" ;;
esac
