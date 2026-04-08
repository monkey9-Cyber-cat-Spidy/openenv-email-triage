import os
import json
import textwrap
from openai import OpenAI

from env import EmailTriageEnvironment
from models import EmailTriageAction

# Mandatory Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")
HF_TOKEN = os.getenv("HF_TOKEN", os.getenv("API_KEY"))

if not HF_TOKEN:
    # Use a dummy for dry-run testing if HF_TOKEN missing locally, 
    # but the instructions state it's mandatory. We raise to follow strict rules.
    raise ValueError("HF_TOKEN environment variable is required")

# Environment vars mapped to variables
TASK_NAME = os.getenv("EMAIL_TASK", "easy")
BENCHMARK = "email_triage"
MAX_STEPS = 15
TEMPERATURE = 0.7

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an AI Email Triage agent.
    Your objective is to route emails to the correct folder ('sales', 'support', 'hr'),
    reply to emails that request it with helpful information, and mark obvious spam.
    
    You must output exactly one JSON object representing your action each turn, matching this schema:
    {
      "action_type": "route" | "reply" | "mark_spam" | "submit",
      "email_id": "id_of_the_email",
      "folder": "destination_folder_name_if_routing",
      "reply_text": "text_of_your_reply_if_replying"
    }
    
    Once the inbox is empty, or you are done, output '{"action_type": "submit"}' to finish.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: list) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    print(f"[END] success={success_val} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(obs_dict):
    return f"Observation: {json.dumps(obs_dict, indent=2)}\n\nWhat is your next action?"

def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    env = EmailTriageEnvironment()
    
    history = []
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Pass the task directly so local environment picks it up
        obs = env.reset(task_name=TASK_NAME)

        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break
                
            obs_dict = {
                "inbox": [{"id": e.id, "subject": e.subject, "body": e.body} for e in obs.inbox],
                "folders": obs.folders,
                "history": obs.last_action_status
            }
            
            user_prompt = build_user_prompt(obs_dict)
            
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"}
                )
                action_text = (completion.choices[0].message.content or "{}").strip()
                action_data = json.loads(action_text)
                action = EmailTriageAction(**action_data)
                
            except Exception as exc:
                # Malformed action or API error
                error = str(exc)
                obs = env.step(EmailTriageAction(action_type="submit"))
                rewards.append(0.0)
                steps_taken = step
                log_step(step=step, action="error", reward=0.0, done=True, error=error)
                break

            # Execute step in environment
            obs = env.step(action)
            
            reward = obs.reward or 0.0
            done = obs.done
            error = None

            rewards.append(reward)
            steps_taken = step

            action_clean = json.dumps(action_data)
            log_step(step=step, action=action_clean, reward=reward, done=done, error=error)

            if done:
                # Final score injected via observe metadata
                score = float(obs.metadata.get("score", 0.0))
                break

        score = min(max(score, 0.0), 1.0)
        success = score >= 0.5  # Considered success if >= 0.5

    finally:
        try:
            env.close()
        except Exception:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()
