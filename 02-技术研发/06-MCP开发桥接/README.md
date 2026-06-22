# MCP 开发桥接 — Claude Code 操控 TD / Unity

> AI 通过 MCP 协议直接操控 TouchDesigner 和 Unity 编辑器，替代手动搭建节点和场景。
> MCP 是**开发时工具**（搭建工程），UDP JSON 是**运行时通信**（Polar H10 → TD/Unity）。两者互补，不替代。

## 架构定位

```
开发时（MCP）                          运行时（UDP JSON @ 10Hz）
┌──────────────────────┐              ┌──────────────────────┐
│  Claude Code         │              │  Python (NK2)        │
│  │                   │              │  Polar H10 → 评分     │
│  ├─ MCP → TD 建节点   │              │  │                   │
│  ├─ MCP → Unity 搭场景 │              │  ├─ UDP:5005 → TD    │
│  └─ MCP → 写C#脚本    │              │  └─ UDP:5006 → Unity │
└──────────────────────┘              └──────────────────────┘
```

---

## 目录

1. [TouchDesigner MCP](./TouchDesigner-MCP操作手册.md) — 12 工具，通过 WebServer DAT 操控 TD
2. [Unity MCP](./Unity-MCP操作手册.md) — 40+ 工具，CoplayDev/unity-mcp v9.7.0
3. [MCP 配置指南](./MCP配置指南.md) — settings.json / .mcp.json / ~/.claude.json
4. [SRP 项目 MCP 工作流](./SRP-MCP工作流.md) — 端到端：从零搭建到闭环

## 快速决策

| 我要... | 用哪个 |
|---------|--------|
| 在 TD 中创建呼吸引导圈节点树 | TD MCP `create_td_node` + `execute_python_script` |
| 在 Unity 中创建 StormScene 场景 | Unity MCP `manage_scene(action="create")` |
| 给 Unity 场景加旅人 Sprite | Unity MCP `manage_gameobject` + `manage_asset` |
| 搭建 TD Panel COMP 监控台 | TD MCP `execute_python_script` |
| 写 Unity C# OSC 接收脚本 | Unity MCP `create_script` + `script_apply_edits` |
| 批量创建 4 个天气场景 | Unity MCP `batch_execute` |

## 环境要求

| 工具 | 版本 | MCP 方案 | 状态 |
|------|------|----------|:----:|
| TouchDesigner | D:\TouchDesigner\bin\TouchDesigner.exe | 8beeeaaat/touchdesigner-mcp v1.4.7 | ✅ 已打开，WebServer `9981` |
| Unity | 6000.4.9f1 @ D:\UnityEngine\6000.4.9f1 | CoplayDev/unity-mcp v9.7.x | ✅ 已打开，MCP HTTP `8083` |
| Python | 3.11+ (~/.hermes-venv) | MCP CLI 客户端 | ✅ |
| Node.js | ~/.hermes/node/ | npx 运行 MCP server | ✅ |

## 2026-06-22 当前实况

| 项 | 状态 | 说明 |
|---|:--:|---|
| TouchDesigner 工程 | ✅ | 已打开 `02-技术研发/03-TouchDesigner/呼吸引导.toe` |
| TD MCP WebServer | ✅ | `127.0.0.1:9981` 可达；GET `/` 返回 NOT_FOUND 属正常路由响应 |
| Unity 工程 | ✅ | 已打开 `02-技术研发/04-Unity视觉/SRP-Weather-Visual` |
| Unity MCP HTTP | ✅ | `127.0.0.1:8083/health` 返回 healthy；MCP 路径为 `/mcp` |
| 项目 `.mcp.json` | ✅ | TD 指向 `9981`，Unity 指向 `http://127.0.0.1:8083/mcp` |
| 运行时 UDP | ⬜ | `5005/5006` 当前未监听；需进入 TD/Unity Play/运行态后再发 mock 数据 |
| Unity MCP 路径状态 | 🟡 | MCPForUnity 运行状态目录出现在乱码路径下，仅含 `Library/MCPForUnity/RunState`，需后续清理或重配 |
