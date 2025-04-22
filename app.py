from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot
import matplotlib.pyplot as plt
import io
import base64
import logging

# ======================================================================================
# Configuration file path
this_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(this_dir, 'rimu_config.json')
# ======================================================================================

# ======================================================================================
# Set up logging
# ======================================================================================
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        watched_files = config.get('watched_files', [])
        rimu_log_file = config.get('rimu_log_file', None)
else:
    watched_files = []
    rimu_log_file = None

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s | %(levelname)5s | %(message)s')
logger = logging.getLogger(__name__)
if rimu_log_file:
    file_handler = logging.FileHandler(rimu_log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)5s | %(message)s'))
    logger.addHandler(file_handler)
    logger.info(f"RIMU log file: {rimu_log_file}")
# ======================================================================================

# ======================================================================================
# Flask app
# ======================================================================================
app = Flask(__name__)
CORS(app)

# ======================================================================================
# Load and save config
# ======================================================================================
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return {}
    
def get_watched_files():
    config = load_config()
    return config.get('watched_files', [])  
    

def save_config(files):
    config = load_config()
    config['watched_files'] = files
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")

# ======================================================================================
# HELPER FUNCTIONS
# ======================================================================================
def _checkFilePath(file_path):
    if not file_path.startswith('/'):
        return os.path.sep + file_path
    return file_path


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
        return jsonify({"error": "File path is required"}), 400
    
    file_path = _checkFilePath(data['file'])
    if not os.path.isfile(file_path):
        return jsonify({"error": "File does not exist"}), 400
    
    files = get_watched_files()
    if file_path not in files:
        files.append(file_path)
        save_config(files)
    
    return jsonify({"message": "File added successfully"})




@app.route('/api/files/delete/<path:file_path>', methods=['GET'])
def remove_file(file_path):
    file_path = _checkFilePath(file_path)
    logger.info(f"Removing file: {file_path}")
    files = get_watched_files()
    if file_path in files:
        files.remove(file_path)
        save_config(files)
        logger.info(f"File removed successfully: {file_path}")
        return jsonify({"message": "File removed successfully"})
    logger.info(f"File not found: {file_path}")
    return jsonify({"error": "File not found"}), 404


@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({"log_files": get_watched_files()})


@app.route('/api/logs/<path:log_path>', methods=['GET'])
def get_log_content(log_path):
    log_path = _checkFilePath(log_path)
    try:
        logger.debug(f"Getting log content for (decoded): {log_path}")
        if not os.path.exists(log_path):
            return jsonify({"error": "File not found"}), 404
            
        with open(log_path, 'r') as f:
            lines = []
            for line in f:
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 3:
                        lines.append([parts[0].strip(), parts[1].strip(), parts[2].strip()])
            return jsonify({"lines": lines})
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/<path:log_path>', methods=['GET'])
def get_analytics(log_path):
    log_path = _checkFilePath(log_path)
    try:
        logger.debug(f"Generating analytics for (decoded): {log_path}")
        
        if not os.path.exists(log_path):
            logger.error(f"File not found for analytics: {log_path}")
            return jsonify({"error": "File not found"}), 404
            
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        levels = {}
        hours = []
        log_levels = []
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split('|')
            if len(parts) >= 3:
                timestamp = parts[0].strip()
                level = parts[1].strip()
                
                try:
                    hour = timestamp.split()[1].split(':')[0]
                    hours.append(hour)
                except:
                    continue
                
                if 'ERROR' in level:
                    levels['ERROR'] = levels.get('ERROR', 0) + 1
                    log_levels.append('ERROR')
                elif 'WARN' in level:
                    levels['WARN'] = levels.get('WARN', 0) + 1
                    log_levels.append('WARN')
                elif 'INFO' in level:
                    levels['INFO'] = levels.get('INFO', 0) + 1
                    log_levels.append('INFO')
                elif 'DEBUG' in level:
                    levels['DEBUG'] = levels.get('DEBUG', 0) + 1
                    log_levels.append('DEBUG')
                else:
                    levels['OTHER'] = levels.get('OTHER', 0) + 1
                    log_levels.append('OTHER')
        
        plt.figure(figsize=(12, 6))
        
        color_map = {
            'ERROR': 'red',
            'WARN': 'orange',
            'INFO': 'blue',
            'DEBUG': 'green',
            'OTHER': 'gray'
        }
        
        import random
        y_values = [random.uniform(0, 1) for _ in range(len(hours))]
        
        for level in set(log_levels):
            indices = [i for i, lvl in enumerate(log_levels) if lvl == level]
            plt.scatter(
                [hours[i] for i in indices],
                [y_values[i] for i in indices],
                c=color_map[level],
                label=level,
                alpha=0.7,
                s=50
            )
        
        plt.title('Log Events by Hour', fontsize=24)
        plt.xlabel('Hour of Day', fontsize=24)
        
        all_hours = sorted(set(hours))
        plt.xticks(all_hours, rotation=45, fontsize=20)
        plt.yticks([])
        
        plt.grid(True, alpha=0.3, axis='both', which='major')
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.legend(fontsize=24)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plot_data = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return jsonify({
            "levels": levels,
            "plot": plot_data
        })
    except Exception as e:
        logger.error(f"Error generating analytics: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 