from openenv.core.env_server.http_server import create_app
from models import EmailTriageAction, EmailTriageObservation
from env import EmailTriageEnvironment

# Create the app with web interface
app = create_app(
    EmailTriageEnvironment,
    EmailTriageAction,
    EmailTriageObservation,
    env_name="email_triage",
    max_concurrent_envs=10
)

# This exposes the required OpenEnv specification endpoints:
# POST /reset
# POST /step
# GET /state
# GET /schema
