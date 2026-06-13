#!/usr/bin/env python3
"""Extract user prompts and preceding agent replies from Codex and Claude logs."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CONTEXT_PROMPT_MARKERS = (
    "# AGENTS.md instructions for ",
    "<environment_context>",
)


@dataclass
class ExtractedMessage:
    role: str
    text: str
    timestamp: str | None
    session_id: str | None
    cwd: str | None
    message_id: str | None


@dataclass
class ParseResult:
    records: list[dict[str, Any]]
    files_scanned: int
    files_with_records: int
    skipped_bad_lines: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract user prompts and previous agent replies from local Codex and Claude Code transcripts."
    )
    parser.add_argument("--source", choices=("all", "codex", "claude"), default="all")
    parser.add_argument("--codex-root", default=str(Path.home() / ".codex"))
    parser.add_argument("--claude-root", default=str(Path.home() / ".claude"))
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--summary", help="Optional Markdown summary path.")
    parser.add_argument("--since", help="Include records at or after YYYY-MM-DD.")
    parser.add_argument("--until", help="Include records before YYYY-MM-DD.")
    parser.add_argument("--max-text-chars", type=int, default=0, help="Truncate prompt/reply text to N chars. 0 keeps full text.")
    parser.add_argument("--max-records", type=int, default=0, help="Limit records after timestamp sorting. 0 keeps all.")
    parser.add_argument("--include-context-prompts", action="store_true", help="Keep AGENTS/environment setup prompts.")
    return parser.parse_args()


def iter_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any] | None]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield line_number, json.loads(stripped)
            except json.JSONDecodeError:
                yield line_number, None


def text_from_content(content: Any, text_keys: tuple[str, ...]) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if not isinstance(item, dict):
                continue
            if item.get("type") in {"tool_result", "tool_use"}:
                continue
            for key in text_keys:
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value)
                    break
        return "\n\n".join(parts)
    if isinstance(content, dict):
        for key in text_keys:
            value = content.get(key)
            if isinstance(value, str):
                return value
    return ""


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def looks_like_context_prompt(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    has_marker = any(marker in stripped for marker in CONTEXT_PROMPT_MARKERS)
    if not has_marker:
        return False
    without_blocks = re.sub(r"<environment_context>.*?</environment_context>", "", stripped, flags=re.S)
    without_blocks = re.sub(r"<INSTRUCTIONS>.*?</INSTRUCTIONS>", "", without_blocks, flags=re.S)
    without_blocks = re.sub(r"# AGENTS\.md instructions for .+?(?=\n\S|\Z)", "", without_blocks, flags=re.S)
    return not without_blocks.strip()


def looks_like_control_prompt(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if stripped.startswith("[Request interrupted by user for tool use]"):
        return True
    if stripped.startswith("<command-name>") and "<command-message>" in stripped:
        return True
    if stripped.startswith("<local-command-stdout>") or stripped.startswith("<local-command-stderr>"):
        return True
    return False


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip() + "\n[TRUNCATED]", True


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def date_bound(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def discover_codex_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for relative in ("sessions", "archived_sessions"):
        base = root / relative
        if base.exists():
            candidates.extend(base.rglob("*.jsonl"))
    return sorted(set(candidates))


def discover_claude_files(root: Path) -> list[Path]:
    projects = root / "projects"
    if not projects.exists():
        return []
    return sorted(projects.rglob("*.jsonl"))


def codex_messages(path: Path, include_context_prompts: bool) -> tuple[list[ExtractedMessage], int]:
    messages: list[ExtractedMessage] = []
    bad_lines = 0
    session_id: str | None = None
    cwd: str | None = None
    for _, obj in iter_jsonl(path):
        if obj is None:
            bad_lines += 1
            continue
        if obj.get("type") == "session_meta":
            payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
            session_id = payload.get("id") if isinstance(payload.get("id"), str) else session_id
            cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else cwd
            continue
        if obj.get("type") != "response_item":
            continue
        payload = obj.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "message":
            continue
        role = payload.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = text_from_content(payload.get("content"), ("text", "input_text", "output_text"))
        text = clean_text(text)
        if not text:
            continue
        if role == "user" and looks_like_control_prompt(text):
            continue
        if role == "user" and not include_context_prompts and looks_like_context_prompt(text):
            continue
        messages.append(
            ExtractedMessage(
                role=role,
                text=text,
                timestamp=obj.get("timestamp") if isinstance(obj.get("timestamp"), str) else None,
                session_id=session_id,
                cwd=cwd,
                message_id=None,
            )
        )
    return messages, bad_lines


def claude_messages(path: Path, include_context_prompts: bool) -> tuple[list[ExtractedMessage], int]:
    messages: list[ExtractedMessage] = []
    bad_lines = 0
    for _, obj in iter_jsonl(path):
        if obj is None:
            bad_lines += 1
            continue
        entry_type = obj.get("type")
        if entry_type not in {"user", "assistant"}:
            continue
        message = obj.get("message")
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue
        if role == "user" and (obj.get("toolUseResult") is not None or obj.get("sourceToolAssistantUUID") is not None):
            continue
        content = message.get("content")
        if role == "user" and isinstance(content, list) and any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content):
            continue
        text = text_from_content(content, ("text", "content"))
        text = clean_text(text)
        if not text:
            continue
        if role == "user" and looks_like_control_prompt(text):
            continue
        if role == "user" and not include_context_prompts and looks_like_context_prompt(text):
            continue
        messages.append(
            ExtractedMessage(
                role=role,
                text=text,
                timestamp=obj.get("timestamp") if isinstance(obj.get("timestamp"), str) else None,
                session_id=obj.get("sessionId") if isinstance(obj.get("sessionId"), str) else None,
                cwd=obj.get("cwd") if isinstance(obj.get("cwd"), str) else None,
                message_id=obj.get("uuid") if isinstance(obj.get("uuid"), str) else None,
            )
        )
    return messages, bad_lines


def records_from_messages(source: str, path: Path, messages: list[ExtractedMessage], max_text_chars: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    assistant_buffer: list[str] = []
    human_prompt_index = 0
    for message in messages:
        if message.role == "assistant":
            assistant_buffer.append(message.text)
            continue
        human_prompt_index += 1
        if not assistant_buffer:
            continue
        previous_reply = clean_text("\n\n".join(assistant_buffer))
        user_prompt, user_truncated = truncate_text(message.text, max_text_chars)
        previous_reply, reply_truncated = truncate_text(previous_reply, max_text_chars)
        records.append(
            {
                "source": source,
                "session_file": str(path),
                "session_id": message.session_id,
                "cwd": message.cwd,
                "timestamp": message.timestamp,
                "turn_index": human_prompt_index,
                "source_message_id": message.message_id,
                "previous_agent_reply": previous_reply,
                "user_prompt": user_prompt,
                "user_prompt_truncated": user_truncated,
                "previous_agent_reply_truncated": reply_truncated,
            }
        )
        assistant_buffer = []
    return records


def filter_records(records: list[dict[str, Any]], since: datetime | None, until: datetime | None) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for record in records:
        timestamp = parse_timestamp(record.get("timestamp"))
        if since and timestamp and timestamp < since:
            continue
        if until and timestamp and timestamp >= until:
            continue
        filtered.append(record)
    return filtered


def parse_all(args: argparse.Namespace) -> ParseResult:
    files: list[tuple[str, Path]] = []
    if args.source in {"all", "codex"}:
        files.extend(("codex", path) for path in discover_codex_files(Path(args.codex_root).expanduser()))
    if args.source in {"all", "claude"}:
        files.extend(("claude", path) for path in discover_claude_files(Path(args.claude_root).expanduser()))

    records: list[dict[str, Any]] = []
    skipped_bad_lines = 0
    files_with_records = 0
    for source, path in files:
        if source == "codex":
            messages, bad_lines = codex_messages(path, args.include_context_prompts)
        else:
            messages, bad_lines = claude_messages(path, args.include_context_prompts)
        skipped_bad_lines += bad_lines
        file_records = records_from_messages(source, path, messages, args.max_text_chars)
        if file_records:
            files_with_records += 1
            records.extend(file_records)

    records = filter_records(records, date_bound(args.since), date_bound(args.until))
    records.sort(key=lambda item: (item.get("timestamp") or "", item.get("source") or "", item.get("session_file") or ""))
    if args.max_records > 0:
        records = records[: args.max_records]
    return ParseResult(records=records, files_scanned=len(files), files_with_records=files_with_records, skipped_bad_lines=skipped_bad_lines)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_summary(path: Path, result: ParseResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    cwd_counts: dict[str, int] = {}
    timestamps = [record.get("timestamp") for record in result.records if record.get("timestamp")]
    for record in result.records:
        counts[record["source"]] = counts.get(record["source"], 0) + 1
        cwd = record.get("cwd") or "unknown"
        cwd_counts[cwd] = cwd_counts.get(cwd, 0) + 1
    top_cwds = sorted(cwd_counts.items(), key=lambda item: item[1], reverse=True)[:20]
    lines = [
        "# Transcript Extraction Summary",
        "",
        f"- Files scanned: {result.files_scanned}",
        f"- Files with extracted records: {result.files_with_records}",
        f"- Extracted records: {len(result.records)}",
        f"- Bad JSONL lines skipped: {result.skipped_bad_lines}",
        f"- Timestamp range: {(min(timestamps) if timestamps else 'unknown')} to {(max(timestamps) if timestamps else 'unknown')}",
        "",
        "## Records By Source",
        "",
    ]
    if counts:
        lines.extend(f"- {source}: {count}" for source, count in sorted(counts.items()))
    else:
        lines.append("- none")
    lines.extend(["", "## Top Working Directories", ""])
    if top_cwds:
        lines.extend(f"- {cwd}: {count}" for cwd, count in top_cwds)
    else:
        lines.append("- none")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = parse_all(args)
    write_jsonl(Path(args.output).expanduser(), result.records)
    if args.summary:
        write_summary(Path(args.summary).expanduser(), result)
    print(f"Extracted {len(result.records)} records from {result.files_scanned} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
