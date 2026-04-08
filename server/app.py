import sys
import os

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openenv.core.env_server.http_server import create_app
from models import EmailTriageAction, EmailTriageObservation
from env import EmailTriageEnvironment
import uvicorn


def main():
    _application = create_app(
        EmailTriageEnvironment,
        EmailTriageAction,
        EmailTriageObservation,
        env_name="email_triage",
        max_concurrent_envs=10
    )
    uvicorn.run(_application, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
