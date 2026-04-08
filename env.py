import uuid
import os
from typing import Dict, Any

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import EmailTriageAction, EmailTriageObservation, Email
from tasks import get_task_data

class EmailTriageEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        super().__init__()
        self._state = State(episode_id=str(uuid.uuid4()), step_count=0)
        self.inbox: Dict[str, Email] = {}
        self.routed: Dict[str, str] = {}
        self.replies: Dict[str, str] = {}
        self.spam: set = set()
        self.folders = ["sales", "support", "hr"]
        self.history = []
        self.grader = None
        self.task_name = "easy"
        
    def reset(self, seed: int = None, episode_id: str = None, **kwargs) -> EmailTriageObservation:
        self._state = State(episode_id=episode_id or str(uuid.uuid4()), step_count=0)
        # We allow overriding the task via kwargs (used by openenv internally) or env var
        self.task_name = kwargs.get("task_name", os.getenv("EMAIL_TASK", "easy"))
        
        emails_list, self.grader = get_task_data(self.task_name)
        
        self.inbox = {e.id: e for e in emails_list}
        self.routed = {}
        self.replies = {}
        self.spam = set()
        self.history = []
        
        return EmailTriageObservation(
            inbox=list(self.inbox.values()),
            folders=self.folders,
            last_action_status="Environment initialised.",
            done=False,
            reward=0.0
        )

    def step(self, action: EmailTriageAction, timeout_s: float = None, **kwargs) -> EmailTriageObservation:
        self._state.step_count += 1
        reward = 0.0
        done = False
        status = ""
        score = 0.0
        
        if action.action_type == "submit":
            done = True
            score = self.grader(self.routed, self.replies, self.spam)
            reward = score
            status = f"Task submitted. Final score: {score:.2f}"
            
        elif action.action_type == "route":
            if action.email_id in self.inbox and action.folder in self.folders:
                self.routed[action.email_id] = action.folder
                del self.inbox[action.email_id]
                reward = 0.1
                status = f"Routed {action.email_id} to {action.folder}"
            else:
                reward = -0.1
                status = f"Failed to route: invalid email_id or folder."
                
        elif action.action_type == "reply":
            if action.email_id in self.inbox and action.reply_text:
                self.replies[action.email_id] = action.reply_text
                del self.inbox[action.email_id]
                reward = 1.0  # Encourage replies
                status = f"Replied to {action.email_id}"
            else:
                reward = -0.1
                status = f"Failed to reply: invalid email_id or empty reply."
                
        elif action.action_type == "mark_spam":
            if action.email_id in self.inbox:
                self.spam.add(action.email_id)
                del self.inbox[action.email_id]
                reward = 0.2
                status = f"Marked {action.email_id} as spam"
            else:
                reward = -0.1
                status = f"Failed to mark spam: invalid email_id."
                
        self.history.append(status)
        
        if not self.inbox and not done:
            done = True
            score = self.grader(self.routed, self.replies, self.spam)
            reward += score
            status += f" | Auto-submitted (inbox empty). Final score: {score:.2f}"

        return EmailTriageObservation(
            inbox=list(self.inbox.values()),
            folders=self.folders,
            last_action_status=status,
            done=done,
            reward=reward,
            metadata={"score": score if done else 0.0}
        )

    @property
    def state(self) -> State:
        return self._state
