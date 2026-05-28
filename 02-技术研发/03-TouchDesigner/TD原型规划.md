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
├── srp_main.toe         主工程
├── tox-files/
│   ├── breath_guide.tox 呼吸引导圈组件
│   ├── prompt_display.tox 提示词组件
│   └── monitor_dashboard.tox 监控台组件
└── assets/
    └── fonts/            提示词用中文字体
```

## Hermes Skill

| 任务 | Skill |
|------|-------|
| TD CHOP 网络设计 | 40-srp-touchdesigner-chop-network |
| UDP 接收 | 40-srp-python-osc-websocket |
