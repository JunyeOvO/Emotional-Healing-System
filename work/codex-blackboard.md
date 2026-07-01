# Codex Blackboard

> Purpose: lightweight project-local working memory for the current task. Keep this file factual, brief, and easy to reset.

## Current Task Goal

整理当前 SRP 项目文件与文档，清除或归档过期文档，修正入口文档中的过期状态与失效引用，保持改动可逆、可审计，并在完成后提交推送。

## Constraints

- 不修改全局 Codex 配置。
- 不安装 hooks。
- 不写入长期 memory。
- 不覆盖已有项目规则。
- 删除或归档前先确认是否为过期、重复或生成文件。
- 保留 SRP 术语边界，避免新增禁用表达。
- 完成后验证文件存在、入口引用有效、`git diff --check` 通过。

## Known Evidence

- `git status --short` 初始为空，当前工作区干净。
- `AGENTS.md` 存在，但顶部阶段仍写“阶段1-需求”，与当前日期和看板不一致。
- 根目录存在 garbled Unity/MCP 运行镜像目录 `02-鎶€鏈爺鍙慭04-Unity瑙嗚`，需判断是否应纳入清理或保持忽略。
- 现有 `work/` 文件属于本地工作流，整理时不应误删。

## Risks

- 误删仍被 Unity/MCP 使用的运行态文件。
- 删除历史阶段文档导致可追溯性下降。
- 只修 README/AGENTS 而遗漏看板、质量门禁等入口引用。
- 清理后未同步索引文档，导致文件存在但无人知道。

## Next-Step Queue

1. 枚举 Markdown、临时文件、生成目录和潜在过期文档。
2. 读取 README、AGENTS、当前看板、质量门禁和交付目录。
3. 确认可删除、可归档、需更新的文件清单。
4. 执行整理并同步入口文档。
5. 验证路径、术语、diff 和 Git 状态。
6. 提交并推送。
