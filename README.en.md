与其放纵AI，不如蒸馏自己！

# myself.skill

`myself.skill` is a Codex skill for distilling a user's local AI interaction history into a practical `SOUL.md` profile. It extracts user prompts and the immediately preceding agent replies from local Codex and Claude Code transcripts, then guides an agent to analyze profession signals, personality, work habits, communication style, technical strengths, collaboration preferences, and guardrails.

This repository contains only the skill implementation. It does not include user transcripts, extracted interactions, analysis results, or a generated `SOUL.md`.

## Features

- Parse local Codex JSONL transcripts from `~/.codex/sessions/**/*.jsonl` and `~/.codex/archived_sessions/**/*.jsonl`
- Parse local Claude Code JSONL transcripts from `~/.claude/projects/**/*.jsonl`
- Extract real user prompts and pair each with the previous agent reply in the same session
- Filter first-turn prompts, tool-result pseudo-prompts, environment injections, and control messages
- Generate `interactions.jsonl` and `summary.md` for downstream analysis
- Provide a structured `SOUL.md` schema for stable personal profile generation

## Installation

Clone the repository into the Codex skills directory as `distill-myself`:

```bash
git clone git@github.com:musnows/myself.skill.git ~/.codex/skills/distill-myself
```

If you cloned it elsewhere, copy it into the skills directory:

```bash
cp -R /path/to/myself.skill ~/.codex/skills/distill-myself
```

## Usage

Invoke it in Codex:

```text
Use $distill-myself to parse my local Codex and Claude Code transcripts, analyze my interaction patterns, and write SOUL.md.
```

The skill will typically start by running:

```bash
python3 ~/.codex/skills/distill-myself/scripts/extract_interactions.py \
  --output .ai-docs/distill-myself/interactions.jsonl \
  --summary .ai-docs/distill-myself/summary.md
```

Useful options:

- `--source codex`: parse Codex transcripts only
- `--source claude`: parse Claude Code transcripts only
- `--since YYYY-MM-DD`: include records at or after a date
- `--until YYYY-MM-DD`: include records before a date
- `--max-text-chars N`: truncate very large prompt/reply fields
- `--include-context-prompts`: keep AGENTS/environment setup prompts

## Output

The extractor writes:

- `interactions.jsonl`: one interaction per line, including `source`, `session_file`, `turn_index`, `previous_agent_reply`, and `user_prompt`
- `summary.md`: source counts, record counts, timestamp range, and top working directories

An agent then uses `references/soul_schema.md` to write `SOUL.md`.

## Privacy

The skill reads local transcripts and writes intermediate files under `.ai-docs/distill-myself/` by default. Do not commit `interactions.jsonl`, `summary.md`, or a generated `SOUL.md` to a public repository unless you have reviewed them for private information.

## Language

中文说明：[README.md](README.md)
