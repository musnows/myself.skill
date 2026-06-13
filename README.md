<div align="center">

与其放纵AI，不如蒸馏自己！

# myself.skill

</div>

`myself.skill` 是一个 Codex skill，用来从本机 Codex 与 Claude Code 对话记录中抽取“用户 prompt + 上一条 agent 回复”，再辅助大模型分析用户的职业信号、性格、工作习惯、说话风格、技能点和协作偏好，最终沉淀成一个 `SOUL.md`。

这个仓库只包含 skill 本身，不包含任何用户会话记录、分析结果或 `SOUL.md`。

## 能力

- 解析本地 Codex JSONL 会话：`~/.codex/sessions/**/*.jsonl`、`~/.codex/archived_sessions/**/*.jsonl`
- 解析本地 Claude Code JSONL 会话：`~/.claude/projects/**/*.jsonl`
- 抽取用户真实 prompt，并配对同会话中上一条 agent 回复
- 自动过滤首轮 prompt、工具结果、环境注入和控制消息
- 生成用于后续分析的 `interactions.jsonl` 与 `summary.md`
- 提供 `SOUL.md` 写作结构，让另一个 agent 能稳定产出个人画像文件

## 安装

把仓库放到 Codex 的 skills 目录，目录名保持为 `distill-myself` 或在 skills 目录下创建同名链接。

```bash
git clone git@github.com:musnows/myself.skill.git ~/.codex/skills/distill-myself
```

如果你已经把仓库 clone 到其他位置，也可以复制目录：

```bash
cp -R /path/to/myself.skill ~/.codex/skills/distill-myself
```

## 使用

在 Codex 中调用：

```text
Use $distill-myself to parse my local Codex and Claude Code transcripts, analyze my interaction patterns, and write SOUL.md.
```

skill 会建议先运行抽取脚本：

```bash
python3 ~/.codex/skills/distill-myself/scripts/extract_interactions.py \
  --output .ai-docs/distill-myself/interactions.jsonl \
  --summary .ai-docs/distill-myself/summary.md
```

常用参数：

- `--source codex`：只解析 Codex 记录
- `--source claude`：只解析 Claude Code 记录
- `--since YYYY-MM-DD`：只分析指定日期之后的记录
- `--until YYYY-MM-DD`：只分析指定日期之前的记录
- `--max-text-chars N`：限制每条 prompt/reply 的最大字符数
- `--include-context-prompts`：保留 AGENTS/environment 这类上下文注入 prompt

## 输出

抽取脚本会生成：

- `interactions.jsonl`：每行一条交互记录，包含 `source`、`session_file`、`turn_index`、`previous_agent_reply`、`user_prompt` 等字段
- `summary.md`：数据源、记录数量、时间范围和高频工作目录摘要

随后 agent 会根据 `references/soul_schema.md` 生成 `SOUL.md`。

## 隐私边界

这个 skill 默认只读本机日志，并把中间产物写到当前项目的 `.ai-docs/distill-myself/`。不要把 `interactions.jsonl`、`summary.md` 或生成的 `SOUL.md` 直接提交到公开仓库，除非你确认其中没有隐私信息。

## 语言

English README: [README.en.md](README.en.md)
