import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TennisAIAnalyzer:
    """Professional & Practical Tennis Tactical Coach using DeepSeek Reasoner"""
    
    def __init__(self):
        try:
            from openai import OpenAI
            # Configure DeepSeek API from environment variables
            self.client = OpenAI(
                base_url="https://api.deepseek.com",
                api_key=os.environ.get("DEEPSEEK_API_KEY", "YOUR_API_KEY_HERE")
            )
            # Use DeepSeek Reasoner for deep tactical analysis
            self.model_name = "deepseek-reasoner"
            self.use_llm = True
        except ImportError:
            self.use_llm = False
    
    def generate_ai_analysis(self, workout_raw_data: Dict) -> str:
        """
        Generate tactical analysis based on the practical prompt
        """
        if not self.use_llm:
            return "⚠️ 分析服务暂时不可用。"
        
        try:
            # The practical prompt provided by user - OPTIMIZED FOR DOUBLES
            system_prompt = "你是一位专业且务实的网球双打战术教练。你对左手持拍、单反球员的特质有深刻理解。请基于客观的生理数据，为我制定高效的双打比赛策略。"
            
            user_prompt = f"""# Player Profile
- **Handedness**: 左手持拍 (Left-handed)
- **Backhand**: 单手反拍 (One-handed backhand)
- **Level**: NTRP 4.0
- **Context**: 这是一场双打比赛 (Doubles Match)。

# Style Guidelines
- **语言风格**：平实、直接、客观。
- **核心要求**：重点分析双打特有的网前配合、左手发球优势及战术布局。拒绝废话，直指本质。
- **篇幅限制**：全文字数控制在 250 字以内。

# Task
第一步：数据有效性检查
如果 `duration`（时长）< 10 分钟 或 `avgHeartRate`（平均心率）< 70 bpm，请直接输出：“**数据无效：时长过短或强度不足，无法进行双打战术分析。**” 并结束回答。如果数据有效，请不要输出任何确认信息，直接跳至第二步。

第二步：双打战术分析
请跳过数据罗列，直接输出以下 3 点：
1. **体能与覆盖率评估**：
   * 结合数据评估在双打快节奏下的体能储备和场上覆盖积极性。
2. **关键生理瓶颈与双打隐患**：
   * 指出最影响双打表现（如网前反应、移动切换）的具体问题。
3. **双打战术调整建议**：
   * 基于左手优势和体能现状，提供具体的双打打法（如 I-Formation、中路封锁、斜线切削压制）。

# Data (JSON)
{json.dumps(workout_raw_data, ensure_ascii=False)}
"""
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"DeepSeek analysis failed: {e}")
            return "⚠️ AI 分析生成失败。"

def analyze_single_workout_with_ai(file_path: str, workout_index: int = 0):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        workouts = data.get("data", {}).get("workouts", [])
        tennis_workouts = [w for w in workouts if "网球" in w.get("name", "")]
        if workout_index < len(tennis_workouts):
            ai_analyzer = TennisAIAnalyzer()
            return ai_analyzer.generate_ai_analysis(tennis_workouts[workout_index])
        return None
    except Exception:
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(analyze_single_workout_with_ai(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 0))
