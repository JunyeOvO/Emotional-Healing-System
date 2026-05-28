# SRP SE — 数据管道 (Sprint 0 v0.1)

> 负责: 生理数据采集 → 信号处理 → 评分模型 → UDP通信 → 系统集成
> 技术栈: Python 3.11 + NeuroKit2 + BioSPPy + bleak + UDP JSON

## 快速启动

```bash
# 激活环境
source ~/.hermes-venv/bin/activate
cd /mnt/c/Users/fujunye/Desktop/Hermes/03-SRP/02-技术研发

# 安装依赖
pip install --proxy http://172.24.48.1:7897 -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 运行模拟数据管道 (60秒)
python main.py --mock --duration 60

# 运行测试
python -m pytest tests/ -v
```

## 模块

| 模块 | 文件 | 功能 |
|------|------|------|
| 数据采集 | 01-数据采集/mock_data.py | 正弦呼吸波 + 模拟ECG (72BPM) |
| 数据采集 | 01-数据采集/ble_connect.py | Polar H10 BLE 连接 (阶段3) |
| 信号处理 | 02-信号处理/signal_pipeline.py | NeuroKit2 滤波+特征提取 |
| 信号处理 | 02-信号处理/scoring_model.py | breath_score + calm_index (0-100) |
| 通信 | 05-通信协议/udp_sender.py | UDP JSON @ 10Hz → :5005(TD) :5006(Unity) |
| 通信 | 05-通信协议/csv_logger.py | 结构化 CSV 日志 |

## 测试

```bash
python -m pytest 01-数据采集/tests/ 02-信号处理/tests/ 05-通信协议/tests/ -v
```

## 依赖关系

```
mock_data.py ──→ signal_pipeline.py ──→ scoring_model.py
                                          │
                              ┌───────────┤
                              ▼           ▼
                       udp_sender.py  csv_logger.py
```

## 版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.2 | 2026-05-27 | Sprint 1: 4天气呼吸+评分, 全链路压测, BLE骨架 |
| v0.1 | 2026-05-26 | Sprint 0: 骨架初始化 |
