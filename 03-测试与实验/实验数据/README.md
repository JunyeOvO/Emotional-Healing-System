# 实验数据目录说明

> 本目录用于存放正式实验或预实验的结构化记录。不要把一次性调试 CSV 当作正式数据提交。

## 数据类型

| 类型 | 是否建议入库 | 说明 |
|---|---|---|
| 正式匿名 CSV 样例 | 可入库 | 必须脱敏，仅用于复现字段结构和图表流程 |
| 原始完整实验数据 | 谨慎 | 优先本地和云端受控备份，提交前确认匿名化和授权边界 |
| mock 调试 CSV | 不入库 | 用于本地调试，已由 `.gitignore` 忽略 |
| 统计图表导出 | 可入库 | 放入测试报告或成果目录，并记录生成脚本 |

## 命名规范

正式实验建议使用：

```text
P{ID}_{weather}_{YYYYMMDD}.csv
```

示例：

```text
P01_storm_20260701.csv
P01_heat_20260701.csv
```

## 最低字段

正式数据至少应包含：

```text
timestamp,frame_id,weather_type,weather_intensity,weather_trend,calm_index,
breath_sync,breath_depth,hrv_coherence,eda_calm,
breath_phase,breath_rate,breath_amplitude,hr,rmssd,eda_tonic,
source_breath,source_cardiac,source_eda,pipeline_latency_ms,operator_mark
```

## 入库前检查

1. 被试编号已匿名化。
2. 文件名不包含真实姓名、联系方式或身份信息。
3. CSV 列与 `02-技术研发/05-通信协议/UDP字段冻结_v1.2.md` 一致。
4. 异常事件已写入 `operator_mark` 或独立异常记录。
5. 数据用途符合“交互状态估计”和情绪调节教育边界。
