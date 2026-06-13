# SOUL.md Schema

Use this structure unless the user asks for a different format.

```markdown
# SOUL

## Identity Snapshot
Write 5-10 bullets summarizing the user's likely professional identity, dominant domains, and interaction intent.

## Profession And Domain Signals
Describe observed work areas, recurring project types, tools, repositories, platforms, and responsibilities. Separate confirmed evidence from inferred roles.

## Personality And Preferences
Describe temperament, decision style, risk tolerance, quality bar, autonomy expectations, and preferred tradeoffs.

## Work Habits
Capture how the user delegates tasks, verifies results, handles ambiguity, asks for changes, reviews work, and manages follow-through.

## Communication Style
Capture language choice, directness, recurring phrases, formatting preferences, correction style, and expected answer shape.

## Technical Skill Map
List the user's evident skills and comfort zones. Include programming ecosystems, tooling, product/ops knowledge, writing/research skills, and domain-specific expertise.

## Collaboration Contract
Write concrete instructions for future agents working with this user. Include what to do by default, what to avoid, when to ask, and how to report results.

## Guardrails And Sensitivities
Record boundaries, privacy expectations, validation requirements, and known failure modes that frustrate the user.

## Evidence And Confidence
Summarize the number and date range of interactions analyzed, sources used, strong evidence, weaker inferences, and gaps.

## Update Protocol
Explain how to refresh this SOUL.md from newer transcripts and what should trigger an update.
```

Writing rules:

- Write in Chinese unless the user requests another language.
- Be specific enough to change agent behavior.
- Do not include long raw prompts or agent replies.
- Do not include secrets, local tokens, private credentials, or unnecessary personal data.
- Prefer "observed pattern" and "likely inference" wording over overconfident labels.
