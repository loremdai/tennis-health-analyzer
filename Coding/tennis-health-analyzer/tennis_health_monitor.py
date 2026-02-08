#!/usr/bin/env python3
"""
Tennis-Specific Health Data Monitor for OpenClaw
INCREMENTAL DETECTION: Only triggers when a NEW Tennis Workout ID is found.
"""

import json
import os
import sys
import time
from datetime import datetime
import logging
from pathlib import Path
import threading
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the script's own directory to sys.path to ensure local imports work
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TennisHealthFileHandler(FileSystemEventHandler):
    def __init__(self, analyzer):
        self.analyzer = analyzer
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            file_path = Path(event.src_path)
            
            # Check if this is today's file
            today = datetime.now().strftime('%Y-%m-%d')
            if today in file_path.name:
                logger.info(f"Health data file modified: {file_path.name}")
                # Add a small delay to ensure file is completely written
                time.sleep(2)
                self.process_file_for_new_tennis(event.src_path)
    
    def _read_json_file(self, file_path):
        """Helper to read JSON with fallback for permission issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (PermissionError, IOError, json.JSONDecodeError) as e:
            logger.warning(f"Standard read/parse failed for {file_path}: {e}. Trying 'cat' fallback.")
            result = subprocess.run(["cat", str(file_path)], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse 'cat' output as JSON: {je}")
            else:
                logger.error(f"Fallback 'cat' failed or empty: {result.stderr}")
            return None

    def process_file_for_new_tennis(self, file_path):
        """Analyze the file and only trigger if a NEW tennis workout ID is found"""
        try:
            # Get the new tennis workout from this file (if any)
            report = self.analyzer.get_new_tennis_workout_report(file_path, self._read_json_file)
            
            if report:
                # We found at least one new tennis workout!
                self.send_analysis_result(report)
                logger.info(f"Successfully processed NEW tennis workout from: {file_path}")
            else:
                logger.info(f"No NEW tennis workouts found in: {Path(file_path).name}")
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def send_analysis_result(self, report):
        """Send the analysis result via DeepSeek Reasoner"""
        try:
            analyses = report.get('analyses', [])
            
            if analyses:
                # Process all new workouts found
                for latest_new_workout in analyses:
                    workout_id = latest_new_workout.get('id', 'Unknown')
                    
                    try:
                        from tennis_ai_analyzer import TennisAIAnalyzer
                        ai_analyzer = TennisAIAnalyzer()
                        
                        # Perform professional analysis
                        ai_report_content = ai_analyzer.generate_ai_analysis(latest_new_workout)
                        
                        # Build final message
                        message = ai_report_content
                        
                        # Save context for interactive chat
                        try:
                            context_data = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "workout_id": workout_id,
                                "raw_workout": latest_new_workout,
                                "ai_report": ai_report_content
                            }
                            context_path = os.path.join(script_dir, "context/latest_match.json")
                            os.makedirs(os.path.dirname(context_path), exist_ok=True)
                            with open(context_path, "w", encoding="utf-8") as f:
                                json.dump(context_data, f, ensure_ascii=False, indent=2)
                        except Exception as ce:
                            logger.error(f"Failed to save context: {ce}")
                        
                        # Send via OpenClaw
                        openclaw_bin = "/Users/daibin/.local/share/fnm/node-versions/v22.22.0/installation/bin/openclaw"
                        node_bin = "/opt/homebrew/bin/node"
                        target_id = "1128305182"
                        cmd = [node_bin, openclaw_bin, "message", "send", "--target", target_id, "--message", message]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        
                        if result.returncode == 0:
                            logger.info(f"Tennis analysis report sent successfully: {result.stdout.strip()}")
                        else:
                            logger.error(f"Failed to send report via CLI. Code: {result.returncode}, Error: {result.stderr.strip()}")
                        
                        # Mark as processed
                        self.analyzer.mark_workout_as_processed(workout_id)
                        
                    except Exception as e:
                        logger.error(f"DeepSeek analysis/delivery failed: {e}")
        except Exception as e:
            logger.error(f"Error in send_analysis_result: {e}")

class TennisHealthDataAnalyzer:
    def __init__(self, watch_dir):
        self.watch_dir = Path(watch_dir)
        self.state_file = "/Users/daibin/.openclaw/tennis_health_analyzer_state.json"
        self.processed_workout_ids = []
        self.load_state()
    
    def load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_workout_ids = state.get('processed_workout_ids', [])
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'processed_workout_ids': self.processed_workout_ids}, f)
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def mark_workout_as_processed(self, workout_id):
        if workout_id not in self.processed_workout_ids:
            self.processed_workout_ids.append(workout_id)
            if len(self.processed_workout_ids) > 100:
                self.processed_workout_ids = self.processed_workout_ids[-100:]
            self.save_state()

    def get_new_tennis_workout_report(self, file_path, read_func):
        """Checks file for tennis workouts and filters out already processed IDs"""
        try:
            data = read_func(file_path)
            if not data:
                return None
            
            workouts = data.get("data", {}).get("workouts", [])
            new_tennis_workouts = []
            for w in workouts:
                name = w.get("name", "")
                workout_id = w.get("id")
                if "网球" in name and workout_id not in self.processed_workout_ids:
                    new_tennis_workouts.append(w)
            
            if not new_tennis_workouts:
                return None
            
            # Sort by start time, get newest first
            def parse_start(w):
                s = w.get("start", "")
                try:
                    return datetime.strptime(s.split(' +')[0], "%Y-%m-%d %H:%M:%S")
                except:
                    return datetime.min
            
            new_tennis_workouts.sort(key=parse_start, reverse=True)
            return {"analyses": new_tennis_workouts}
        except Exception as e:
            logger.error(f"Error checking for new tennis data: {e}")
            return None

def run_monitor():
    watch_dir = Path("/Users/daibin/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/iCloud 自动化/")
    if not watch_dir.exists():
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return
    analyzer = TennisHealthDataAnalyzer(watch_dir)
    event_handler = TennisHealthFileHandler(analyzer)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()
    logger.info(f"Started tennis professional monitor for: {watch_dir}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_monitor()
