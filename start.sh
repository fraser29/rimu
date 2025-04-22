#!/bin/bash

# Default ports
BACKEND_PORT=5000
FRONTEND_PORT=3000

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --backend-port)
      BACKEND_PORT="$2"
      shift 2
      ;;
    --frontend-port)
      FRONTEND_PORT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create a temporary file to store PIDs
PID_FILE=$(mktemp)
trap 'rm -f "$PID_FILE"' EXIT

# Function to start backend
start_backend() {
    echo "Starting backend on port $BACKEND_PORT..."
    cd "$(dirname "$0")"
    export FLASK_APP=app.py
    export FLASK_ENV=development
    flask run --port=$BACKEND_PORT &
    echo $! >> "$PID_FILE"
}

# Function to start frontend
start_frontend() {
    echo "Starting frontend on port $FRONTEND_PORT..."
    cd frontend
    export PORT=$FRONTEND_PORT
    npm start &
    echo $! >> "$PID_FILE"
}

# Function to stop all services
stop_services() {
    echo -e "\nStopping services..."
    
    # Read PIDs from file and kill processes
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid..."
            # First try graceful shutdown
            kill -TERM "$pid" 2>/dev/null
            
            # Wait for process to terminate
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force stopping process $pid..."
                kill -KILL "$pid" 2>/dev/null
            fi
        fi
    done < "$PID_FILE"
    
    # Clear PID file
    > "$PID_FILE"
    echo "All services stopped."
    exit 0
}

# Set up signal handlers
trap stop_services SIGINT SIGTERM

# Start services
start_backend
start_frontend

echo -e "\nServices started successfully!"
echo "Press Ctrl+C to stop all services"
echo "Backend running on: http://localhost:$BACKEND_PORT"
echo "Frontend running on: http://localhost:$FRONTEND_PORT"

# Wait for any process to exit
wait -n
stop_services 