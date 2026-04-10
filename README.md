---
title: OpenEnv Email Triage
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 📧 Email Triage — OpenEnv Environment

> **Meta PyTorch Hackathon × Scaler School of Technology**
> An original multi-task reinforcement learning environment for evaluating LLM email triage agents.

---

## Environment Overview and Motivation

**Email Triage** is a universal, high-frequency knowledge-worker task. Every professional triages email daily — routing messages, flagging spam, and composing context-aware replies. Yet no standardised RL environment exists for this task.

This environment tests an LLM agent's ability to:
- **Understand context** — distinguish sales enquiries from HR notices from support tickets
- **Detect malice** — identify spam/phishing from realistic email patterns
- **Compose replies** — generate professional responses under time pressure
- **Prioritise** — handle VIP clients and urgent escalations before routine mail

The environment is fully original and purpose-built for this hackathon. It is not derived from any existing OpenEnv sample or public repository.

---

## Action and Observation Spaces

### Observation Space
Each observation is a JSON object containing:
| Field | Type | Description |
|---|---|---|
| `inbox` | list | Emails remaining to process. Each has `id`, `sender`, `subject`, `body` |
| `folders` | list | Available routing folders: `["sales", "support", "hr"]` |
| `last_action_status` | str | Result of the previous action (feedback for the agent) |

### Action Space
The agent emits one JSON object per step:
| Field | Values | Required for |
|---|---|---|
| `action_type` | `"route"` / `"reply"` / `"mark_spam"` / `"submit"` | always |
| `email_id` | email ID string | route, reply, mark_spam |
| `folder` | `"sales"` / `"support"` / `"hr"` | route only |
| `reply_text` | string | reply only |

---

## Tasks

### Easy (`task_id=easy`)
- **3 emails**, clearly categorised by subject and body
- Expected: route e1→sales, e2→hr, e3→support
- **Grader:** `0.05 + (correct_routes / 3) × 0.90` → range `[0.05, 0.95]`

### Medium (`task_id=medium`)
- **5 emails**: routing + spam detection + reply required
- Expected: route m3/m4/m5, mark m1 as spam, reply to urgent ticket m2
- **Grader:** partial credit per component, base 0.10 → range `[0.10, 0.95]`

### Hard (`task_id=hard`)
- **10 emails**: multiple spam, overlapping domains, VIP hidden in context
- Expected: 3 spam detected, 4 routes correct, VIP client reply
- **Grader:** spam +0.08 each, routes +0.10 each, VIP reply +0.30 → range `[0.05, 0.95]`

All graders return **partial credit** — every correct action earns reward, enabling meaningful RL training signal across the full difficulty spectrum.

---

## Reward Structure

Rewards are returned at every step (not just episode end), providing a dense training signal:

| Action | Reward |
|---|---|
| Correct route | +0.20 |
| Correct spam | +0.10 |
| Reply to email needing reply | +0.15 |
| Wrong route | −0.05 |
| False positive spam | −0.10 |
| Submit | Final grader score applied |

Final episode score is always in **(0.0, 1.0)** exclusive — never exactly 0 or 1.

---

## Setup and Usage

### Run on Hugging Face Spaces
The environment is live at: https://huggingface.co/spaces/Monkeysaur/openenv-email-triage

```bash
# Reset (start a new episode)
curl -X POST https://monkeysaur-openenv-email-triage.hf.space/reset \
     -H "Content-Type: application/json" \
     -d '{"task_id": "easy"}'

# Step (take an action)
curl -X POST https://monkeysaur-openenv-email-triage.hf.space/step \
     -H "Content-Type: application/json" \
     -d '{"action": {"action_type": "route", "email_id": "e1", "folder": "sales"}}'

# List available tasks
curl https://monkeysaur-openenv-email-triage.hf.space/tasks
```

### Run with Docker locally
```bash
docker build -t openenv-email-triage .
docker run -p 7860:7860 openenv-email-triage
```

### Run the baseline inference script
```bash
pip install -r requirements.txt
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your_hf_token"
python inference.py
```

The script runs all 3 tasks sequentially and emits structured logs:
```
[START] task=easy env=email_triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action={"action_type":"route","email_id":"e1","folder":"sales"} reward=0.20 done=false error=null
[STEP] step=2 ...
[END] success=true steps=3 score=0.65 rewards=0.20,0.20,0.25
```

---

## Baseline Performance (Qwen2.5-72B-Instruct)

| Task | Typical Score | Notes |
|---|---|---|
| Easy | 0.65 – 0.95 | Routing is straightforward |
| Medium | 0.44 – 0.78 | Spam + reply together trips weaker models |
| Hard | 0.13 – 0.69 | VIP context reasoning is the bottleneck |

Scores vary between runs due to LLM temperature, but graders are fully deterministic.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/reset` | POST | Start a new episode (accepts `task_id`) |
| `/step` | POST | Execute one action |
| `/state` | GET | Get current environment state |
| `/tasks` | GET | List available task IDs |
| `/health` | GET | Health check |
| `/schema` | GET | Action/observation JSON schemas |
| `/metadata` | GET | Environment metadata |
| `/ws` | WebSocket | Persistent session endpoint |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_BASE_URL` | Yes | LLM API endpoint |
| `MODEL_NAME` | Yes | Model identifier |
| `HF_TOKEN` | Yes | Hugging Face API key |
