# TouchDesigner 原型规划

> 呼吸引导圈 + 提示词动画 + 实验监控台 + 实时数据曲线

## 四大模块

| 模块 | 功能 | 输入 | 输出 |
|------|------|------|------|
| 呼吸引导圈 | 视觉呼吸引导（缩放/颜色） | breath.phase + guidance.target_breath_rate | 动画圈 |
| 提示词动画 | 环境文字浮现/消散 | guidance.prompt + weather.transition | 粒子文字 |
| 实验监控台 | 主试视角全局监控 | 全部 UDP JSON 字段 | 仪表盘 |
| 实时数据曲线 | 呼吸/HR/calm_index 折线图 | breath/calm/hrv 时间序列 | CHOP 曲线 |

## 技术要点

- UDP In DAT 接收 JSON → 解析 → 分发到各 CHOP
- 呼吸圈动画：circle_radius 驱动 Transform CHOP
- 天气强度 → 背景颜色/粒子密度渐变
- 监控台用 Panel COMP 布局

## 文件结构（规划）

```
03-TouchDesigner/
├── srp_main.toe             主工程
├── osc_bridge/              ← 新增: OSC 遥控桥接
│   ├── osc_controller.py    外部 Python OSC 控制器
│   ├── td_osc_receiver.py   TD 内部 Execute DAT 脚本
│   └── README.md            搭建指南
├── tox-files/
│   ├── breath_guide.tox     呼吸引导圈组件
│   ├── prompt_display.tox   提示词组件
│   └── monitor_dashboard.tox 监控台组件
└── assets/
    └── fonts/               提示词用中文字体
```

## OSC 远程遥控方案 ✅

```
外部 Python (hermes-venv)           TouchDesigner
┌────────────────────┐    OSC     ┌──────────────────────┐
│  osc_controller.py │ ──UDP:7000→│ OSC In DAT (oscin1)  │
│                    │           │ Execute DAT (exec_osc)│
│  par / exec / create│           │ td.op().par().val     │
└────────────────────┘           └──────────────────────┘
```

### 快速开始

1. **TD 内准备**: 拖入 OSC In DAT → port 7000, 拖入 Execute DAT → 加载 `td_osc_receiver.py`
2. **外部操控**: `python osc_controller.py` → 互动模式, 或 `python osc_controller.py ping` 测试
3. **一键骨架**: `python osc_controller.py srp` 自动创建 SRP 节点树

## Hermes Skill

| 任务 | Skill |
|------|-------|
| TD CHOP 网络设计 | 40-srp-touchdesigner-chop-network |
| UDP 接收 | 40-srp-python-osc-websocket |
