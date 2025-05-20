from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
import logging
from dateutil.parser import parse
import datetime
# ======================================================================================
# Configuration file path
this_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(this_dir, 'rimu_config.json')
CONFIG_FILE_WATCHING = os.path.join(this_dir, 'rimu_config_watching.json')
# ======================================================================================

# ======================================================================================
# Set up logging
# ======================================================================================
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        rimu_log_file = config.get('rimu_log_file', None)
        LOG_LEVEL = config.get('LOG_LEVEL', 'INFO')
else:
    rimu_log_file = None
    LOG_LEVEL = 'INFO'

# Create a custom filter to exclude /api/logs from Flask's access logs
class LogFilter(logging.Filter):
    def filter(self, record):
        return not ('GET /api/logs' in record.getMessage())

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# Set up console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)5s | %(message)s'))
console_handler.addFilter(LogFilter())  # Add the filter to console handler
logger.addHandler(console_handler)
logger.info(f"Logging to console")

if rimu_log_file:
    file_handler = logging.FileHandler(rimu_log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)5s | %(message)s'))
    file_handler.addFilter(LogFilter())  # Add the filter to file handler
    logger.addHandler(file_handler)
    logger.info(f"Logging to RIMU log file: {rimu_log_file}")

# ======================================================================================
# Flask app
# ======================================================================================
app = Flask(__name__)
CORS(app)

# Disable Flask's default logging
app.logger.disabled = True
logging.getLogger('werkzeug').disabled = True

# ======================================================================================
# Load and save config
# ======================================================================================
def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}
    
def get_watched_files(LOG=True):
    config = load_config(CONFIG_FILE_WATCHING)
    if LOG or LOG_LEVEL == 'DEBUG':
        logger.info(f"Loaded config from {CONFIG_FILE_WATCHING} ({len(config.get('watched_files', []))} log files being watched)")
    return config.get('watched_files', [])

def save_config(files):
    config = load_config(CONFIG_FILE_WATCHING)
    config['watched_files'] = files
    try:
        with open(CONFIG_FILE_WATCHING, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Saved config to {CONFIG_FILE_WATCHING} ({len(files)} log files being watched)")
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")

# ======================================================================================
# HELPER FUNCTIONS
# ======================================================================================
def _checkFilePath(file_path):
    if not file_path.startswith('/'):
        return os.path.sep + file_path
    return file_path

def _get_short_name(file_path):
    # Get the filename without extension
    return os.path.splitext(os.path.basename(file_path))[0]

# ======================================================================================
# API endpoints
# ======================================================================================
@app.route('/api/files', methods=['GET'])
def get_files():
    return jsonify({"files": get_watched_files()})

@app.route('/api/files', methods=['POST'])
def add_file():
    data = request.json
    if 'file' not in data:
        # don't actually get here - caught at web level
        return jsonify({"error": "File path is required - paste into input box"}), 400
    
    file_path = _checkFilePath(data['file'])
    if not os.path.isfile(file_path):
        logger.error(f"File does not exist: {file_path}")
        return jsonify({"error": "File does not exist"}), 400
    
    files = get_watched_files()
    # Check if file already exists in the list
    if not any(f['full_path'] == file_path for f in files):
        files.append({
            'short_name': _get_short_name(file_path),
            'full_path': file_path
        })
        save_config(files)
        logger.info(f"File added successfully: {file_path}")
    return jsonify({"message": "File added successfully"})

@app.route('/api/files/delete/<path:file_path>', methods=['GET'])
def remove_file(file_path):
    file_path = _checkFilePath(file_path)
    logger.info(f"Removing file: {file_path}")
    files = get_watched_files()
    files = [f for f in files if f['full_path'] != file_path]
    save_config(files)
    logger.info(f"File removed successfully: {file_path}")
    return jsonify({"message": "File removed successfully"})

def convert_time_to_ISO(timestamp_str: str) -> str:
    # Convert timestamp to ISO format
    # Example: 2025-05-19 12:00:00 -> 2025-05-19T12:00:00Z
    try:
        timestamp = parse(timestamp_str, fuzzy=True)
        return timestamp.isoformat() + 'Z'
    except ValueError as e:
        logger.error(f"Error converting time to ISO: {str(e)}")
        return None

def _findDelimiter(line):
    if line.count(' | ') in [2,3]:
        return ' | '
    elif line.count(' - ') in [2,3]:
        return ' - '
    elif line.count(' : ') in [2,3]:
        return ' : '
    elif line.count('|') in [2,3]:
        return '|'
    elif line.count('-') in [2,3]:
        return '-'
    elif line.count(':') in [2,3]:
        return ':'
    return None

def _findLevelColumn(line_parts):
    for k1, part in enumerate(line_parts):
        if part.strip() in ['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL']:
            return k1
    return None


@app.route('/api/logs/<path:log_path>', methods=['GET'])
def get_log_content(log_path):
    log_path = _checkFilePath(log_path)
    try:
        logger.debug(f"Getting log content for (decoded): {log_path}")
        if not os.path.exists(log_path):
            return jsonify({"error": "File not found"}), 404
        
        delimiter, level_column = None, None
        with open(log_path, 'r') as f:
            lines = []
            for line in f:
                if line.strip():
                    if delimiter is None:
                        delimiter = _findDelimiter(line)
                    if delimiter is None:
                        logger.error(f"No delimiter found for line: {line}")
                        raise Exception(f"No delimiter found for log file: {log_path}")
                    parts = line.split(delimiter)
                    level_column = _findLevelColumn(parts)
                    if len(parts) == 3:
                        # timestamp, level, message
                        lines.append([convert_time_to_ISO(parts[0].strip()), parts[level_column].strip(), parts[2].strip()])
                    elif len(parts) == 4:
                        # timestamp, level, source, message - Skip the source for now. 
                        lines.append([convert_time_to_ISO(parts[0].strip()), parts[level_column].strip(), parts[3].strip()])
            return jsonify({"lines": lines})
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        files = get_watched_files(LOG=False)
        if not files:
            return jsonify({"error": "No files being watched"}), 404

        plt.figure(figsize=(12, 6))
        
        # Colors for different files
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for idx, file_path_dict in enumerate(files):
            file_path = file_path_dict['full_path']
            if not os.path.exists(file_path):
                continue

            log_content = get_log_content(file_path)
            if log_content.status_code != 200:
                continue
            lines = log_content.json['lines']
            
            # Count entries per hour
            hourly_counts = {}
            for line in lines:
                # Each line is time(iso), level, message
                timestamp = datetime.datetime.fromisoformat(line[0])
                date_str = timestamp.strftime("%Y%m%d")
                hour = timestamp.hour
                key = f"{date_str} {hour}:00"
                hourly_counts[key] = hourly_counts.get(key, 0) + 1

            if not hourly_counts:
                continue
                
            # Sort by datetime
            sorted_times = sorted(hourly_counts.keys())
            counts = [hourly_counts[time] for time in sorted_times]
            
            # Plot with smoothing
            
            # Convert times to numerical values for smoothing
            x = np.arange(len(sorted_times))
            y = counts
            
            # Plot the smooth curve
            plt.plot(x, y, 
                    label=os.path.basename(file_path),
                    color=colors[idx % len(colors)],
                    alpha=0.7,
                    linewidth=2)
            
            # Add actual data points
            plt.scatter(x, y, 
                       color=colors[idx % len(colors)],
                       alpha=0.5,
                       s=30)
        
        plt.title('Log Entries per Hour', fontsize=24)
        plt.xlabel('Time', fontsize=20)
        plt.ylabel('Number of Entries', fontsize=20)
        
        # Set x-axis ticks to show every hour
        plt.xticks(x, sorted_times, rotation=45, fontsize=12)
        plt.yticks(fontsize=12)
        
        # Add grid and legend
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=12)
        plt.tight_layout()
        
        # Convert plot to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plot_data = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return jsonify({
            "plot": plot_data
        })
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 