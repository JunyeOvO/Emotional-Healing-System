# 03-SRP — 多模态交互情绪疗愈 (SRP v2.1)

> 可穿戴呼吸/HRV → 实时桥接 → 视听反馈 → 情绪调节教育
> 2026/5/20 — 6/30 | 4人团队 | 当前阶段：**阶段1-需求**

## 快速入口

| 我要... | 打开 |
|---------|------|
| 看项目全貌 | `PROJECT_FRAMEWORK.md` 或 `00-项目管理/项目规约/SRP项目规划书.docx` |
| 看当前任务 | `00-项目管理/看板与进度/当前阶段看板.md` |
| 看天气设计 | `01-需求与设计/情绪天气方案/四种天气设计.md` |
| 看设备方案 | `02-技术研发/01-数据采集/设备方案.md` |
| 看评分模型 | `02-技术研发/02-信号处理/评分模型设计.md` |
| 看通信协议 | `02-技术研发/05-通信协议/UDP协议定义.md` |
| 看实验方案 | `03-测试与实验/实验方案/实验设计.md` |
| 查文献 | `srp参考文献/` (85篇, 5类) |

## 项目结构

```
03-SRP/
├── CLAUDE.md                    ← 本文件
├── PROJECT_FRAMEWORK.md         企业框架 (322行, 完整规划)
├── README.md                    快速说明
├── 00-项目管理/
│   ├── 项目规约/SRP项目规划书.docx  原始规划文档 (7.4MB)
│   └── 看板与进度/当前阶段看板.md  任务跟踪 + 阶段状态
├── 01-需求与设计/
│   └── 情绪天气方案/四种天气设计.md 4种天气→呼吸策略→视觉要素
├── 02-技术研发/
│   ├── 01-数据采集/设备方案.md      Polar H10 + 呼吸胸带
│   ├── 02-信号处理/评分模型设计.md   4维独立评分 (breath_sync/depth/hrv_coherence/eda_calm)
│   ├── 03-TouchDesigner/TD原型规划.md 引导圈+提示词+监控台
│   ├── 04-Unity视觉/场景设计.md      4天气场景+旅人Sprite
│   └── 05-通信协议/UDP协议定义.md     JSON @ 10Hz
├── 03-测试与实验/
│   ├── 实验方案/实验设计.md       8-12被试, 被试内设计
│   └── 实验数据/                (采集后填充)
├── 04-成果与交付/               (阶段7填充)
└── srp参考文献/
    ├── 01-research-proposal/    10篇 综述/meta
    ├── 02-biosignal-hrv-eeg/    15篇 HRV/EEG
    ├── 04-gamification-emotion/ 35篇 游戏化/情绪/屏幕交互
    ├── 05-clinical-reference/   10篇 临床参考
    └── missing_downloads.txt    78篇待下载
```

## Hermes Skill 快速调用

```bash
# 启动新阶段
加载: 40-srp-wearable-chief → project-intake-plan

# 文献检索
加载: 40-srp-literature-review → background-research-pipeline

# 信号处理开发
加载: 40-srp-biosignal-processing, 40-srp-device-selection

# TouchDesigner 开发
加载: 40-srp-touchdesigner-chop-network, 40-srp-python-osc-websocket

# Unity 2D 开发
加载: 40-srp-unity-osc-runtime, 40-srp-animation-state-machine, 40-srp-feedback-mapping-design, 40-srp-2d-pixel-visual-design

# 实验与交付
加载: 40-srp-experiment-design, 40-srp-reporting-standard
      deliverable-quality-gate, evidence-audit-and-citation

# Git 操作
加载: 40-srp-git-and-review → github-pr-branch-workflow
```

## 关键约束

- 所有文档用「交互状态估计」替代「生理状态诊断」
- 禁止出现：诊断、治疗、疾病、患者、医疗设备、临床
- 消费级设备数据不作严肃判断依据
- 提示词从环境自然出现，不用角色说教
- 每种天气只做一个核心视觉机制

## 环境依赖

| 工具 | 用途 | 状态 |
|------|------|:--:|
| Python 3.14 + NeuroKit2 | 信号处理 | ✅ |
| Polar H10 BLE | 心电采集 | ⬜ 待采购 |
| 呼吸胸带 | 呼吸采集 | ⬜ 待选型 |
| TouchDesigner | 实时可视化 | ✅ D:\TouchDesigner\bin\TouchDesigner.exe |
| Unity 6000.4.9f1 | 2D像素渲染 | ✅ D:\UnityEngine\6000.4.9f1\Editor\Unity.exe |
