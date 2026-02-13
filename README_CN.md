# TennisHealth-AW

[English](README.md) | [中文](README_CN.md)

**基于 Apple Watch 采集与 DeepSeek AI 推理的职业级网球运动分析助手。**

将消费级穿戴数据提升为“ATP 教练级”的战术洞察。不仅仅是简单的平均值统计，TennisHealth-AW 深入挖掘时序数据中的微观变化——心率漂移、步频衰减、每步能量消耗——通过 AI 实时复盘，告诉你身体状态如何影响了今天的战术执行。

---

## 核心功能

### 1. 零点击全自动闭环
- **iCloud 无缝同步**: 后台监听 Health Auto Export 自动导出的健康数据。
- **智能筛选**: 自动识别时长 > 5 分钟的网球记录，触发 AI 分析。
- **即时战术推送**: 打完球几分钟内，一份 5 点核心战术报告通过 OpenClaw (ClawdBot) 推送到你手上。

### 2. 职业级运动科学 (ATP 指标)
基于时序数据衍生出普通 App 不提供的深度指标：
- **TRIMP (训练冲量)**: 量化单场真实生理负荷，超越卡路里的表面数据。
- **心血管效率 (Cardiac Efficiency)**: 实时计算心率/步频比，精准捕捉疲劳引发的移动能力衰减。
- **运动经济性**: 分析每一步的能量消耗 (kJ/step)，评估动作效率。
- **HRR1 (心率恢复)**: 1 分钟心率下降值，作为心肺适能的核心评判标准。
- **SPM 时序分析**: 逐分钟步频追踪，定位比赛后半程的体能崩盘点。

### 3. LLM 交互式复盘
不仅仅是接收报告，你还可以与数据对话：
> *“对比一下今天第一盘和决胜盘的心血管效率，看看我体能是不是崩了？”*
> *“最近三周我的高强度区间 (Zone 3) 占比有提高吗？”*

---

## 系统架构

```
Apple Watch  -->  iPhone HealthKit  -->  Health Auto Export  -->  iCloud JSON
                  (蓝牙同步)              (自动导出)              (iCloud云盘)
                                                                     |
                                             +-----------------------+
                                             |                       |
                                        daemon/                 skills/
                                       (后台推送)              (交互问答)
                                             |                       |
                                        DeepSeek AI            LLM 客户端
                                             |              (Cursor/Claude)
                                      OpenClaw 推送
```

## 项目结构

| 目录 | 说明 |
|---|---|
| `daemon/` | 后台守护进程，负责 Watchdog 监听和 OpenClaw 推送。 |
| `skills/` | **LLM Skill 定义**。`skill.md` 教会 AI 如何读取和分析你的历史数据。 |
| `tools/` | 核心业务逻辑：`workout_filter.py` (数据 ETL) 和 `ai_analyzer.py` (ATP 指标计算与 Prompt)。 |
| `examples/`| 样例 JSON 数据，用于 schema 参考。 |

## 快速开始

### 环境依赖
- Python 3.10+
- macOS (必须，依赖 iCloud Drive 及 TCC 权限回退机制)
- [Health Auto Export](https://apps.apple.com/app/health-auto-export/id1115567461) (iPhone App)

### 安装步骤

1. 克隆项目并安装依赖：
   ```bash
   git clone https://github.com/loremdai/TennisHealth-AW.git
   cd TennisHealth-AW
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   export DEEPSEEK_API_KEY="your_api_key_here"
   ```

3. 配置路径：
   修改 `daemon/health_monitor.py` 顶部的变量 (`ICLOUD_DIR`, `OPENCLAW_BIN` 等) 以匹配你的本地环境。

### 使用方法

**方式 A: 后台守护模式 (自动推送)**
启动监控进程：
```bash
python daemon/health_monitor.py
```
*建议使用 `nohup` 或配置为 macOS LaunchAgent 开机自启。*

**方式 B: 交互问答模式 (LLM Skill)**
1. 在 Cursor 或 Claude Desktop 中打开本项目。
2. 模型会自动读取 `skills/tennis_health/skill.md`，你只需自然语言提问即可查询历史表现。

---

## 核心分析维度

AI 分析引擎针对网球运动优化，覆盖 5+1 个关键维度：

1. **强度与负荷**: TRIMP 值、心率区间 (Zone 1/2/3) 分布、心率动态范围。
2. **移动效率**: SPM (步频) 时序衰减、心血管效率指数。
3. **能量经济性**: 每步能量消耗趋势、代谢功率分布。
4. **恢复能力**: HRR1 (1分钟恢复值)、跨场次恢复趋势。
5. **战术建议**: 基于身体状态 (如左手持拍、单反) 的针对性战术调整。
6. **跨场衰减**: (多场次日) 疲劳累积模型分析。

---

## OpenClaw 集成

本项目针对 [OpenClaw](https://github.com/nicepkg/openclaw) 深度设计。

守护进程利用 OpenClaw CLI 将分析报告直接推送至你常用的即时通讯软件。请确保已安装并登录：

```bash
npm install -g openclaw
openclaw login
```

---

## 许可证

MIT
