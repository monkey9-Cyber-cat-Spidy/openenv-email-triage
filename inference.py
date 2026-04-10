#!/usr/bin/env python3
"""
OpenEnv Email Triage — Inference Script

Runs the agent against all 3 tasks (easy, medium, hard) and emits structured
stdout logs in the [START] / [STEP] / [END] format required by the hackathon.

Required env vars:
    API_BASE_URL  — LLM endpoint (e.g. https://router.huggingface.co/v1)
    MODEL_NAME    — Model identifier (e.g. Qwen/Qwen2.5-72B-Instruct)
    HF_TOKEN      — Hugging Face API token (used as the API key)
"""

import os
import json
import textwrap
from openai import OpenAI

from env import EmailTriageEnvironment
from models import EmailTriageAction
from tasks import TASK_IDS

# ── Mandatory environment variables ─────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN",     os.getenv("API_KEY", ""))

if not HF_TOKEN:
    raise ValueError("HF_TOKEN environment variable is required")

# ── Config ───────────────────────────────────────────────────────────────────
BENCHMARK   = "email_triage"
MAX_STEPS   = 15
TEMPERATURE = 0.2

SYSTEM_PROMPT = textwrap.dedent("""
    You are an AI Email Triage agent.
    Your objective is to route emails to the correct folder ('sales', 'support', 'hr'),
    reply to emails that request it with helpful information, and mark obvious spam.

    You must output exactly one JSON object per turn matching this schema:
    {
      "action_type": "route" | "reply" | "mark_spam" | "submit",
      "email_id":    "id_of_the_email",
      "folder":      "destination_folder_if_routing",
      "reply_text":  "text_of_reply_if_replying"
    }

    Once the inbox is empty or you are done, output {"action_type": "submit"}.
""").strip()

# ── Log helpers ───────────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    err  = error if error else "null"
    done_s = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_s} error={err}",
          flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list) -> None:
    rewards_s  = ",".join(f"{r:.2f}" for r in rewards)
    success_s  = str(success).lower()
    print(f"[END] success={success_s} steps={steps} score={score:.2f} rewards={rewards_s}",
          flush=True)

# ── Single-task episode ───────────────────────────────────────────────────────
def run_task(client: OpenAI, task_name: str) -> None:
    env     = EmailTriageEnvironment()
    rewards = []
    steps_taken = 0
    score   = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env.reset(task_name=task_name)
        history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            obs_dict = {
                "inbox":   [{"id": e.id, "subject": e.subject, "body": e.body}
                             for e in obs.inbox],
                "folders":  obs.folders,
                "status":   obs.last_action_status,
            }
            history.append({"role": "user",
                             "content": f"Observation:\n{json.dumps(obs_dict, indent=2)}\n\nNext action?"})

            try:
                resp = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=history,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"},
                )
                action_text = (resp.choices[0].message.content or "{}").strip()
                history.append({"role": "assistant", "content": action_text})
                action_data = json.loads(action_text)
                action = EmailTriageAction(**action_data)

            except Exception as exc:
                err_msg = str(exc)[:120]
                action  = EmailTriageAction(action_type="submit")
                obs     = env.step(action)
                rewards.append(float(obs.reward or 0.0))
                steps_taken = step
                log_step(step=step, action="error", reward=float(obs.reward or 0.0),
                         done=True, error=err_msg)
                break

            obs = env.step(action)
            reward = float(obs.reward or 0.0)
            done   = obs.done
            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=json.dumps(action_data),
                     reward=reward, done=done, error=None)

            if done:
                score = float(obs.metadata.get("score", 0.0))
                break

        # Clamp score strictly inside (0, 1)
        score   = round(min(max(score, 0.05), 0.95), 4)
        success = score >= 0.5

    finally:
        try:
            env.close()
        except Exception:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    # Run all tasks — evaluator expects one [START]..[END] block per task
    for task_name in TASK_IDS:          # ["easy", "medium", "hard"]
        run_task(client, task_name)


if __name__ == "__main__":
    main()
