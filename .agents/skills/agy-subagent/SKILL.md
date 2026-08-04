---
name: agy-subagent
description: Execute persistent background subagents via the Antigravity CLI (agy) for non-backend coding tasks (QA, code review, test execution, frontend design, documentation). Use when running tasks via CLI subagents in the Antigravity IDE.
---

# `agy-subagent` — CLI Subagent Orchestration Skill

This skill teaches the agent how to launch and maintain **persistent, role-specific subagents** via the `agy` CLI for non-backend engineering tasks (QA, code review, test plan execution, frontend work, documentation).

---

## 1. When to Use CLI Subagents vs Main Agent

| Task Scope | Handled By | Method |
|---|---|---|
| **Backend Rust / C++ Core Logic** | **Main Agent** | Direct code edits & local compilation |
| **QA / Auditing / Verification** | **QA Subagent (`qa-engineer`)** | Persistent `agy` Subagent |
| **Adversarial Code Review** | **Review Subagent (`review`)** | Persistent `agy` Subagent |
| **Frontend Design / React / CSS** | **Frontend Subagent (`frontend-engineer`)** | Persistent `agy` Subagent |
| **Documentation & Feature Ledgers**| **Docs Subagent (`docs`)** | Persistent `agy` Subagent |

---

## 2. Mandatory Model & CLI Parameters

Whenever invoking `agy` for a subagent task, **ALWAYS** pass these exact flags:

```bash
--model gemini-3.6-flash-high --dangerously-skip-permissions
```

---

## 3. Persistent Subagent Lifecycle Pattern

Subagents are **persistent across the entire conversation thread**. Never spawn a duplicate subagent if an active conversation ID already exists for that role!

### Step 1: Initializing a Role Subagent (First Turn)
Run `agy` with the role instructions and capture the newly generated conversation ID:

```bash
# Launch QA Subagent
agy -p "You are the QA Subagent. Read .agents/rules/qa-engineer.md first. Your task: <TASK_DESCRIPTION>" \
    --model gemini-3.6-flash-high \
    --dangerously-skip-permissions

# Extract Conversation ID for persistence
ls -t ~/.gemini/antigravity-cli/conversations/*.db | head -n 1 | xargs -I {} basename {} .db
```

Store the returned UUID (e.g. `qa_conv_id = "5132d509-a16d-4d34-9237-d6e60d617015"`).

### Step 2: Reusing the Persistent Subagent (Subsequent Turns)
For all subsequent tasks assigned to the same role in the thread, reuse the stored conversation ID:

```bash
agy --conversation <STORED_CONVERSATION_ID> \
    -p "Follow-up QA task: Verify the latest benchmark results in app/src-tauri/benches/" \
    --model gemini-3.6-flash-high \
    --dangerously-skip-permissions
```

---

## 4. Role Execution Protocols

### A. QA & Test Audit (`qa-engineer`)
- **First Prompt**: `"You are the QA Engineer. Read .agents/rules/qa-engineer.md first. Perform a full test audit across app/src-tauri/ and report test coverage and benchmark results."`
- **Rule**: Never allow mock data or swallowed assertions. Verify empirical exit codes.

### B. Code Review (`review`)
- **First Prompt**: `"You are the Senior Reviewer. Read .agents/rules/code-style-guide.md first. Perform an adversarial code review of recent changes in src/ and output diffs or improvements."`

### C. Frontend Engineer (`frontend-engineer`)
- **First Prompt**: `"You are the Frontend Engineer. Read .agents/rules/frontend-engineer.md first. Implement modern UI/CSS design guidelines in app/src/."`

---

## 5. Summary Checklist for Main Agent
1. Check if a conversation ID already exists for the target role (`qa`, `review`, `frontend`, `docs`).
2. If NEW: Launch `agy -p "..."`, save the new UUID.
3. If EXISTING: Pass `--conversation <UUID> -p "..."`.
4. Always pass `--model gemini-3.6-flash-high --dangerously-skip-permissions`.
