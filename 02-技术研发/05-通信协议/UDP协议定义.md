# UDP JSON 通信协议

> Python → TouchDesigner / Unity 实时数据传输

## 协议规范

- **传输层**：UDP
- **编码**：JSON
- **频率**：10Hz（每100ms一帧）
- **端口**：TD:5005, Unity:5006

## 消息格式

```json
{
  "version": "1.0",
  "timestamp": 1716300000.123,
  "breath": {
    "score": 72.5,
    "rate": 14.2,
    "depth": 0.65,
    "phase": "inhale",
    "guidance_phase": "hold"
  },
  "calm": {
    "index": 68.3,
    "trend": "improving",
    "weather_intensity": 0.32
  },
  "hrv": {
    "hr": 72,
    "rmssd": 45.2,
    "coherence": 0.58
  },
  "weather": {
    "type": "storm",
    "intensity": 0.32,
    "transition": "weakening"
  },
  "guidance": {
    "prompt": "慢慢吸气...4秒",
    "circle_radius": 0.8,
    "target_breath_rate": 10
  }
}
```

## 字段说明

| 字段 | 范围 | 说明 |
|------|:----:|------|
| breath.score | 0-100 | 呼吸同步度 |
| calm.index | 0-100 | 综合平静指数 |
| calm.weather_intensity | 0-1 | 1=恶劣天气, 0=晴天 |
| breath.phase | inhale/hold/exhale | 当前呼吸阶段 |
| weather.transition | weakening/stable/intensifying | 天气变化趋势 |

## Hermes Skill

| 任务 | Skill |
|------|-------|
| Python OSC/WebSocket | 40-srp-python-osc-websocket |
| TD 接收端 | 40-srp-touchdesigner-chop-network |
| Unity 接收端 | 40-srp-unity-osc-runtime |
