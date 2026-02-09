#!/usr/bin/env python3
"""
Tennis-Specific Health Data Monitor for OpenClaw
PRECISION MODE: 3-min threshold, Conclusion-first analysis, CLI delivery.
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

# Ensure local imports work
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
            today = datetime.now().strftime('%Y-%m-%d')
            if today in file_path.name:
                logger.info(f"Health file update detected: {file_path.name}")
                time.sleep(2) # Buffer for write completion
                self.process_file_for_new_tennis(event.src_path)
    
    def _read_json_file(self, file_path):
        """Robust JSON read with cat fallback for iCloud TCC issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (PermissionError, IOError, json.JSONDecodeError) as e:
            logger.warning(f"Standard read failed for {file_path}: {e}. Using 'cat' fallback.")
            result = subprocess.run(["cat", str(file_path)], capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return None
            return None

    def process_file_for_new_tennis(self, file_path):
        try:
            report = self.analyzer.get_new_tennis_workout_report(file_path, self._read_json_file)
            if report:
                self.send_analysis_result(report)
                logger.info(f"Reported NEW tennis workout(s) from {file_path}")
            else:
                logger.info(f"No NEW valid tennis workouts (>3min) in {Path(file_path).name}")
        except Exception as e:
            logger.error(f"Processing error: {e}")
    
    def send_analysis_result(self, report):
        """Send conclusion-first tactical analysis via DeepSeek"""
        try:
            analyses = report.get('analyses', [])
            for workout in analyses:
                workout_id = workout.get('id', 'Unknown')
                try:
                    from tennis_ai_analyzer import TennisAIAnalyzer
                    ai_analyzer = TennisAIAnalyzer()
                    
                    # AI Analysis with Conclusion-First instructions
                    ai_report_content = ai_analyzer.generate_ai_analysis(workout)
                    
                    # Save context
                    try:
                        context_path = os.path.join(script_dir, "context/latest_match.json")
                        os.makedirs(os.path.dirname(context_path), exist_ok=True)
                        with open(context_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "workout_id": workout_id,
                                "raw_workout": workout,
                                "ai_report": ai_report_content
                            }, f, ensure_ascii=False, indent=2)
                    except Exception: pass
                    
                    # Deliver via CLI
                    openclaw_bin = "/Users/daibin/.local/share/fnm/node-versions/v22.22.0/installation/bin/openclaw"
                    node_bin = "/opt/homebrew/bin/node"
                    target_id = "1128305182"
                    cmd = [node_bin, openclaw_bin, "message", "send", "--target", target_id, "--message", ai_report_content]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        logger.info(f"Notification sent for {workout_id}")
                        self.analyzer.mark_workout_as_processed(workout_id)
                    else:
                        logger.error(f"CLI Send Error: {result.stderr.strip()}")
                        
                except Exception as e:
                    logger.error(f"Analysis loop failure: {e}")
        except Exception as e:
            logger.error(f"send_analysis_result error: {e}")

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
        except Exception: pass
    
    def save_state(self):
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({'processed_workout_ids': self.processed_workout_ids}, f)
        except Exception: pass

    def mark_workout_as_processed(self, workout_id):
        if workout_id not in self.processed_workout_ids:
            self.processed_workout_ids.append(workout_id)
            if len(self.processed_workout_ids) > 200:
                self.processed_workout_ids = self.processed_workout_ids[-200:]
            self.save_state()

    def get_new_tennis_workout_report(self, file_path, read_func):
        try:
            data = read_func(file_path)
            if not data: return None
            
            workouts = data.get("data", {}).get("workouts", [])
            new_ones = []
            for w in workouts:
                # Name contains "网球" AND duration > 3 mins AND ID not seen
                if "网球" in w.get("name", "") and w.get("duration", 0) > 180 and w.get("id") not in self.processed_workout_ids:
                    new_ones.append(w)
            
            if not new_ones: return None
            # Sort chronologically
            new_ones.sort(key=lambda x: x.get("start", ""))
            return {"analyses": new_ones}
        except Exception as e:
            logger.error(f"Check error: {e}")
            return None

def run_monitor():
    watch_dir = Path("/Users/daibin/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/iCloud 自动化/")
    analyzer = TennisHealthDataAnalyzer(watch_dir)
    event_handler = TennisHealthFileHandler(analyzer)
    observer = Observer()
    observer.schedule(event_handler, str(watch_dir), recursive=False)
    observer.start()
    logger.info("Started Tennis Monitor (NOHUP/FDA Mode)")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run_monitor()
