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

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Flask server:
```bash
python app.py
```

The backend will run on http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The frontend will run on http://localhost:3000

## Usage

1. Open the application in your web browser
2. Use the file selector in the left panel to add log files
3. Click on a log file to view its contents
4. Use the filter box to search through logs
5. View analytics and visualizations in the right panel

## Configuration

Log file paths are stored in `rimu_config.json`. This file is automatically created and updated when you add new log files through the interface.
