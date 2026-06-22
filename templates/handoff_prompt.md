# Handoff Prompt

Use this prompt when opening a new conversation or handing the workspace to
another agent.

```text
你在 <absolute workspace path> 继续 Paper-WorkFlow 项目 <short name>。
先读：
1. 00_meta/handoff/<latest-card>.md
2. 00_meta/workflow_state.json
3. 00_meta/stage_passport.md

Fresh Reality Check:
- 先跑 git status / git log -3（若工作区在 git repo 内）。
- 刷新 workflow_state.json、stage_passport.md 和当前阶段关键产物。
- 不要把 handoff card 当作当前事实。

本段目标：<one concrete objective>。
Completion Criteria：<observable proof, command, gate, or file>.
收尾要求：更新 workflow_state.json、stage_passport.md，新建下一张 handoff card，并打印下一段启动提示词。
```
