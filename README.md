---
title: OpenEnv Email Triage
emoji: 📧
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Email Triage OpenEnv Environment

## Environment Overview and Motivation
This environment simulates a real-world task performed by knowledge workers every day: **Email Triage**.
Users must sort incoming emails into predefined folders (Sales, Support, HR) and provide meaningful replies to urgent or specific requests, while ignoring and marking explicit spam. The motivation is to test an LLM's capability to understand context, route appropriately, identify malicious content, and formulate professional replies based on surrounding text.

## Action and Observation Spaces

### Observation Space
The observation space is a JSON representation containing:
- `inbox`: A list of emails presently in the inbox. Each email contains:
  - `id`: Unique string identifier
  - `sender`: Email address of the sender
  - `subject`: Email subject
  - `body`: Body text of the email
- `folders`: A list of available routing folders (e.g., `["sales", "support", "hr"]`)
- `last_action_status`: A text status output indicating the result of the prior action.

### Action Space
The agent produces a single JSON object corresponding to this structure:
- `action_type`: One of `"route"`, `"reply"`, `"mark_spam"`, or `"submit"`.
- `email_id`: The ID of the targeted email.
- `folder`: The destination folder (required for `"route"`).
- `reply_text`: The body of the reply (required for `"reply"`).

## Task Descriptions

1. **Easy Task (`task=easy`)**
   - **Difficulty:** Easy
   - **Description:** Route 3 clearly delineated emails into the Sales, HR, and Support folders. All signals are distinct and obvious.

2. **Medium Task (`task=medium`)**
   - **Difficulty:** Medium
   - **Description:** Route 5 emails. The agent must identify 1 spam email and mark it accordingly. The agent must also identify an urgent ticket and issue a reply rather than just routing.

3. **Hard Task (`task=hard`)**
   - **Difficulty:** Hard
   - **Description:** Route 10 emails with overlapping terminology. Multiple spam pieces must be identified. The agent must reply to a VIP client whose details are hidden in a secondary email thread within the inbox.

## Setup and Usage Instructions

### Docker Execution
To run via Docker (as expected on Hugging Face Spaces):
```bash
docker build -t openenv-email-triage .
docker run -p 7860:7860 openenv-email-triage
```

### Local Execution
To run the baseline locally:
```bash
pip install -r requirements.txt
export HF_TOKEN="your_token"
export EMAIL_TASK="easy" # Change to 'medium' or 'hard' to run different tasks
python inference.py
```

## Baseline Performance Scores
Baseline runs using `gpt-4o-mini` consistently yield the following scores:
- **Easy**: 1.00 score
- **Medium**: 1.00 score 
- **Hard**: 0.8+ score (Depending on reply specificity logic)
