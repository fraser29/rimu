# RIMU - Log Viewer Dashboard

A simple lightweight web-based dashboard for viewing and analyzing log files.

## Features

- Interface for adding log files for watching
- Left panel showing all available log files
- Main panel displaying log content with filtering capabilities
- Right panel showing analytics and visualizations (basic for now)
- Real-time filtering
- Updates currently via "refresh" button

## Setup

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

### Start the backend and frontend

A single script is provided for convenience to start the backend and frontend. Have python environment activated and run:

```bash
./start.sh
# OR
./start.sh --backend-port 5001 --frontend-port 3001
```

To stop the services:
- Press Ctrl+C
- The script will attempt a graceful shutdown first
- If processes don't terminate within 5 seconds, it will force kill them
- You'll see status messages about what's happening during shutdown

### Start frontend and backend independently

1. Start the Flask server:
```bash
python app.py
```

The backend will run on http://localhost:5000 by default.

2. Start the development server:
```bash
cd frontend
npm start
```

The frontend will run on http://localhost:3000 by default.

## Usage

1. Open the application in your web browser at http://localhost:3000
2. Use the input field in the left panel to add log files (copy and paste full path to the log file)
3. Click on a log file to view its contents
4. Use the filter box to search through logs
5. View analytics and visualizations in the right panel

## Configuration

Log file paths are stored in `rimu_config_watching.json`. This file is automatically created and updated when you add new log files through the interface.

The main log file is stored in `rimu_config.json`. Create this file and set entry "rimu_log_file" to the path of the log file you want to use as the main log file. 
