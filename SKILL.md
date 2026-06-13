---
name: distill-myself
description: Extract and analyze a user's local Codex and Claude Code transcripts to distill their profession signals, personality, work habits, communication style, technical strengths, collaboration preferences, and guardrails into a SOUL.md profile. Use when the user asks to "distill me", "蒸馏我自己", generate a SOUL.md, infer user traits from local AI conversation history, or build a durable personal profile from Codex/Claude logs.
---

# Distill Myself

## Workflow

1. Decide the output location. If the user provides a path, use it. Otherwise write the final `SOUL.md` in the current working directory and keep intermediate files under `.ai-docs/distill-myself/`.
2. Run `scripts/extract_interactions.py` to parse local Codex and Claude Code transcripts. Use `python3` by default; if it is unavailable, try `python`:

```bash
python3 /Users/mothra/.codex/skills/distill-myself/scripts/extract_interactions.py \
  --output .ai-docs/distill-myself/interactions.jsonl \
  --summary .ai-docs/distill-myself/summary.md
```

3. Inspect `summary.md` first, then read `interactions.jsonl` directly or in chunks. Each JSONL record contains a user prompt plus the immediately preceding agent reply for that session turn. Session-first prompts and tool-result pseudo-prompts are skipped.
4. Read `references/soul_schema.md` before writing `SOUL.md`.
5. Analyze repeated behavior, not isolated messages. Distinguish direct evidence from inference, and avoid exposing secrets, tokens, private URLs, or unnecessary raw transcript dumps.
6. Write `SOUL.md` as a practical profile another agent can use. Focus on profession signals, personality, work habits, communication style, skill map, collaboration preferences, guardrails, and evidence confidence.

## Extraction Notes

- Default Codex sources: `~/.codex/sessions/**/*.jsonl` and `~/.codex/archived_sessions/**/*.jsonl`.
- Default Claude Code source: `~/.claude/projects/**/*.jsonl`.
- Use `--source codex` or `--source claude` to limit extraction.
- Use `--since YYYY-MM-DD` and `--until YYYY-MM-DD` to bound analysis by transcript timestamps.
- Use `--max-text-chars N` to truncate very large turns in the extracted JSONL while preserving truncation flags.
- Use `--include-context-prompts` only when AGENTS/environment setup prompts should be analyzed as user behavior; by default they are skipped.

## Analysis Rules

- Treat transcript data as private local material. Do not publish it, paste large raw excerpts, or send it to external tools unless the user explicitly asks.
- Prefer stable patterns across many turns over dramatic one-off statements.
- Capture user speech patterns verbatim only in short examples and only when useful.
- Mark uncertain conclusions as tentative.
- Keep `SOUL.md` useful for future agents: concise, operational, and evidence-grounded.
