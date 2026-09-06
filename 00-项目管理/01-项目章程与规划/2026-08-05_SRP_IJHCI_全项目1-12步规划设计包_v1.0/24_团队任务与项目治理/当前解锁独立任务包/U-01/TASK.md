# U-01 【Unity】可靠控制技术探针与渲染回执

> 状态权威仍是[05_可领取任务包.csv](../../05_可领取任务包.csv)。本包输入为生成时快照，实际修改必须发生在`FILES.md`列出的项目权威路径。

## 领取登记

- 领取人：Codex
- 分支：`codex/u-01-unity-control`
- 第二复核人：傅钧烨（团队总监，独立第二人复核人）
- 领取时间：历史登记未记录；当前不得重复领取

## 任务边界

- 领域：Unity
- 波次：W1
- 状态：`IN_REVIEW`
- 类型：FIXED
- 预计工作量：4人日
- 前置依赖：F-01、F-03、F-05、P-01
- 所需技能：Unity+C#+TCP/UDP+状态镜像+幂等
- 涉及文件与工作目录：见[FILES.md](FILES.md)

## 学习资料

- [L-UNITY Unity中文手册](https://docs.unity3d.com/cn/2023.2/Manual/index.html)
- [L-UNITYTEST Unity Test Framework中文手册](https://docs.unity3d.com/cn/2023.2/Manual/testing-editortestsrunner.html)

## 交付物

- SessionMirror
- 可靠控制客户端
- UDP5006接收门
- ACK
- 渲染回执
- 重连与故障注入

## 四阶段过程

1. 读取依赖制品并先建立失败测试或golden fixture。
2. 只在所属模块内实现最小完整纵向能力。
3. 运行正常、异常、重连或权限负测试。
4. 整理代码、文档、证据并提交第二人验收。

## 验收要求

- [x] AC1丢包乱序重复fixture测试通过且控制重发保持同一事件ID
- [x] AC2旧帧不覆盖新帧且Unity本地时钟不推进模块
- [x] AC3握手错误断连重连和回执拒绝均按合同失败关闭

## 必需证据

- [x] Edit/Play测试
- [x] 网络故障日志
- [x] 状态镜像轨迹
- [x] ACK与渲染回执序列

## 完成条件

合同版本与F-01和F-05一致且消费已签收P-01传输输出并向U-03交付技术探针

完成还必须满足：第二人复核、相关验证通过、证据路径可访问，并完成本任务范围内的commit与push。

## 完成回填

- 实际改动文件：见`FILES.md`列出的项目权威路径
- 验证命令与结果：技术候选已完成；模型复核状态`PENDING`
- 证据路径：`03-测试与实验/F-03_技术验收记录_已签署.md`
- commit：`6c09f71d14bcb0288a4b83f87b177975c49bfe3d`
- push目标：`origin/codex/u-01-unity-control`
- 真实团队第二人复核：`PENDING`
- 剩余风险：傅钧烨签收仍开放；任务文档列明的外部边界仍开放
