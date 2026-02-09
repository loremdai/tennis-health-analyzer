import json
import os
import sys
import subprocess
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TennisTimeAnalyzer:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=os.environ.get("DEEPSEEK_API_KEY")
        )
        self.model_name = "deepseek-reasoner"

    def analyze_period(self, start_ts, end_ts):
        """Analyze all tennis matches between start_ts and end_ts - FOCUS ON SUMMARY ONLY"""
        try:
            start_dt = datetime.fromisoformat(start_ts.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_ts.replace('Z', '+00:00'))
            
            date_str = start_dt.strftime('%Y-%m-%d')
            file_path = f"/Users/daibin/Library/Mobile Documents/iCloud~com~ifunography~HealthExport/Documents/iCloud 自动化/HealthAutoExport-{date_str}.json"
            
            result = subprocess.run(["cat", file_path], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return f"❌ 无法读取数据文件。"
            
            data = json.loads(result.stdout)
            workouts = data.get("data", {}).get("workouts", [])
            period_workouts = []

            for w in workouts:
                if "网球" not in w.get("name", ""):
                    continue
                w_start_str = w.get("start", "").split(' +')[0]
                try:
                    w_dt = datetime.strptime(w_start_str, "%Y-%m-%d %H:%M:%S")
                    if start_dt.replace(tzinfo=None) <= w_dt <= end_dt.replace(tzinfo=None):
                        if w.get("duration", 0) > 180:
                            period_workouts.append(w)
                except Exception:
                    continue

            if not period_workouts:
                return f"🔍 在该时间段内未发现有效记录。"

            # UPDATED PROMPT: NO ADVICE, PURE PERFORMANCE SUMMARY
            prompt = f"""你是一位职业网球体能分析师。请对以下在 {date_str} 完成的 {len(period_workouts)} 场网球运动进行【赛后生理复盘与数据总结】。

# 要求：
1. **全天数据结算**：统计累计时长、总消耗卡路里、全天平均心率、全天峰值心率。
2. **体能衰减模型分析**：对比第一场与最后一场的关键指标变化。重点分析【心率/步频比】的变化趋势，以此论证疲劳对移动能力的具体影响。
3. **表现特征总结**：客观总结今天这几场比赛呈现出的生理特征（例如：高心率耐受型、晚期爆发型等）。
4. **拒绝任何建议**：不要给出“建议下次如何打”之类的话语，只针对已经发生的数据进行深度归纳。
5. **字数限制**：300 字以内，平实、严谨。

# 原始数据 (JSON)：
{json.dumps(period_workouts, ensure_ascii=False)}
"""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位专注于数据复盘的职业网球体能分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content

        except Exception as e:
            return f"❌ 汇总分析失败: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    analyzer = TennisTimeAnalyzer()
    print(analyzer.analyze_period(sys.argv[1], sys.argv[2]))
