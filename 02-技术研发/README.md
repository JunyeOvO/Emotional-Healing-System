# SRP SE — 数据管道与实时桥接 (v1.2)

> 负责: 生理数据采集 → 信号处理 → 评分模型 → UDP通信 → 系统集成
> 技术栈: Python 3.11 + NeuroKit2 + BioSPPy + bleak + UDP JSON/OSC

## 快速启动

```bash
# Windows PowerShell
cd 02-技术研发

# 安装依赖
pip install -r requirements.txt

# 运行模拟数据管道 (60秒, 终端1)
python main.py --weather storm --duration 60

# 实时可视化仪表盘 (终端2)
python visualizer.py

# 运行测试
python -m pytest tests/ -v
```

## 模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 数据采集 | 01-数据采集/mock_data.py | 正弦呼吸波 + 模拟ECG (72BPM) |
| 数据采集 | 01-数据采集/device_driver.py | 真实设备驱动抽象 |
| 数据采集 | 01-数据采集/device_manager.py | 设备管理与缓冲读取 |
| 数据采集 | 01-数据采集/ble_device.py | BLE设备接入骨架 |
| 信号处理 | 02-信号处理/signal_pipeline.py | NeuroKit2 滤波+特征提取 |
| 信号处理 | 02-信号处理/scoring_model.py | 4-dim scoring (breath_sync/depth/hrv_coherence/eda_calm) + calm_index |
| 通信 | 05-通信协议/udp_sender.py | UDP JSON v1.2 @ 10Hz → :5005(TD) :5006(Unity) |
| 通信 | 05-通信协议/osc_sender.py | OSC 桥接输出 |
| 通信 | 05-通信协议/csv_logger.py | 结构化 CSV 日志 |
| 可视化 | visualizer.py | 4面板实时仪表盘 (监听UDP 5005) |
| TD桥接 | 03-TouchDesigner/osc_bridge/ | OSC 远程遥控 TD 工程 |
| Unity视觉 | 04-Unity视觉/SRP-Weather-Visual/ | Unity 2D 天气视觉工程 |

## 测试

```bash
python -m pytest 01-数据采集/tests/ 02-信号处理/tests/ 05-通信协议/tests/ -v
```

## 依赖关系

```
mock_data.py ──→ signal_pipeline.py ──→ scoring_model.py
                                          │
                              ┌───────────┼────────────┐
                              ▼           ▼            ▼
                       udp_sender.py  osc_sender.py  csv_logger.py
```

## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2 | 2026-06-22 | UDP v1.2元数据、真实设备骨架、Unity/TD桥接状态同步 |
| v0.3 | 2026-05-28 | OSC远程遥控桥接 + 实时可视化仪表盘 |
| v0.2 | 2026-05-27 | Sprint 1: 4天气呼吸+评分, 全链路压测, BLE骨架 |
| v0.1 | 2026-05-26 | Sprint 0: 骨架初始化 |
