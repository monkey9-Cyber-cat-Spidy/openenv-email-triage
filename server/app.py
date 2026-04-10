import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.http_server import create_app
from models import EmailTriageAction, EmailTriageObservation
from env import EmailTriageEnvironment
from tasks import TASK_IDS
import uvicorn

# Create the app at module level (required by OpenEnv multi-mode spec)
app = create_app(
    EmailTriageEnvironment,
    EmailTriageAction,
    EmailTriageObservation,
    env_name="email_triage",
    max_concurrent_envs=10
)


# Custom /tasks endpoint so the hackathon evaluator can enumerate available tasks
@app.get("/tasks")
def list_tasks():
    """Return the list of available task IDs for this environment."""
    return {
        "tasks": [
            {"id": "easy",   "description": "Route 3 emails to correct folders"},
            {"id": "medium", "description": "Route emails, detect spam, write a reply"},
            {"id": "hard",   "description": "Handle 10 emails: spam, VIP reply, routing"},
        ]
    }


def main():
    """
    Entry point for direct execution via uv run or python -m server.app.

    pyproject.toml [project.scripts] entry: server = "server.app:main"
    """
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
