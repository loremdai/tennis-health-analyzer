# TennisHealth-AW

[English](README.md) | [中文](README_CN.md)

**Automated Physiological & Tactical Analysis for Tennis Enthusiasts via Apple Watch & AI.**

TennisHealth-AW bridges the gap between raw Apple Watch data and professional-grade tennis coaching. By leveraging LLMs (DeepSeek Reasoner), it transforms your heart rate, movement, and energy metrics into actionable tactical insights, delivered instantly after your match.

---

## Features

### 1. Zero-Click Automation
- **Auto-Sync**: Monitors iCloud for new workout exports from Health Auto Export.
- **Auto-Analysis**: Automatically filters for "Tennis" workouts (>5 min) and triggers AI analysis.
- **Push Notification**: Delivers a concise 5-point tactical report via OpenClaw (ClawdBot) immediately after play.

### 2. Pro-Level Sports Science (ATP Metrics)
Goes beyond basic averages by deriving advanced metrics from time-series data:
- **TRIMP (Training Impulse)**: Quantifies true physiological load.
- **Cardiac Efficiency**: Tracks HR/Step ratio to detect fatigue-induced movement decay.
- **Specific Power**: Analyzes energy cost per step (kJ/step) for movement economy.
- **HRR (Heart Rate Recovery)**: Evaluates cardiovascular fitness via 1-minute recovery rates.
- **SPM Analysis**: Time-series analysis of Steps Per Minute to pinpoint intensity drops.

### 3. Interactive Coaching (LLM Skill)
Feed the raw data to your LLM client (Cursor/Claude) to ask complex questions:
> *"Compare my cardiac efficiency between the first and last set today."*
> *"Did my recovery rate improve over the last 3 matches?"*

---

## Architecture

```
Apple Watch  -->  iPhone HealthKit  -->  Health Auto Export  -->  iCloud JSON
                  (Bluetooth)             (Auto-Export)           (Cloud Drive)
                                                                     |
                                             +-----------------------+
                                             |                       |
                                        daemon/                 skills/
                                     (Auto-Push)           (Interactive)
                                             |                       |
                                        DeepSeek AI            LLM Client
                                             |              (Cursor/Claude)
                                      OpenClaw Push
```

## Project Structure

| Directory | Description |
|---|---|
| `daemon/` | Background service for monitoring files and pushing notifications. |
| `skills/` | **LLM Skill** definitions. `skill.md` teaches LLMs how to read & analyze your data. |
| `tools/` | Core logic: `workout_filter.py` (ETL) and `ai_analyzer.py` (ATP Metrics & Prompting). |
| `examples/`| Sample JSON data for testing and schema reference. |

## Quick Start

### Prerequisites
- Python 3.10+
- macOS (Required for iCloud Drive access & TCC workaround)
- [Health Auto Export](https://apps.apple.com/app/health-auto-export/id1115567461) (iPhone App)

### Installation

1. Clone and install dependencies:
   ```bash
   git clone https://github.com/loremdai/TennisHealth-AW.git
   cd TennisHealth-AW
   pip install -r requirements.txt
   ```

2. Configure Environment:
   ```bash
   export DEEPSEEK_API_KEY="your_api_key_here"
   ```

3. Configure Paths:
   Edit `daemon/health_monitor.py` variables (`ICLOUD_DIR`, `OPENCLAW_BIN`, etc.) to match your local setup.

### Usage

**Option A: Daemon Mode (Auto-Push)**
Start the background monitor:
```bash
python daemon/health_monitor.py
```
*Tip: Use `nohup` or a LaunchAgent to keep it running.*

**Option B: Interactive Mode (LLM Skill)**
1. Open this project in Cursor or Claude Desktop.
2. The `skills/tennis_health/skill.md` file will guide the AI to answer your questions about your historical data.

---

## Analysis Dimensions

The AI analyzer is prompt-engineered to focus on 5+1 key dimensions:

1. **Intensity & Load**: TRIMP, HR Zones (1/2/3), Dynamic Range.
2. **Movement Efficiency**: SPM time-series, Cardiac Efficiency Index.
3. **Energy Economy**: Energy cost per step, metabolic power distribution.
4. **Recovery**: HRR1 (1-min recovery), inter-match recovery trends.
5. **Tactics**: Left-handed/One-handed backhand specific advice based on physical status.
6. **Cross-Match Decay**: (For multi-match days) Fatigue trend analysis.

---

## Integration with OpenClaw

This project is designed to work seamlessly with [OpenClaw](https://github.com/nicepkg/openclaw).

The `daemon` uses the OpenClaw CLI to push the analysis report to your preferred instant messenger app. Ensure you have OpenClaw installed and logged in:

```bash
npm install -g openclaw
openclaw login
```

---

## License

MIT
