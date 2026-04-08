from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from openenv.core.env_server.types import Action, Observation

class Email(BaseModel):
    id: str = Field(description="Unique identifier for the email")
    sender: str = Field(description="Sender of the email")
    subject: str = Field(description="Subject line")
    body: str = Field(description="Content of the email")

class EmailTriageAction(Action):
    action_type: Literal["route", "reply", "mark_spam", "submit"] = Field(
        ..., description="Type of action: 'route', 'reply', 'mark_spam', or 'submit' to finish the task."
    )
    email_id: Optional[str] = Field(None, description="The ID of the email to operate on")
    folder: Optional[str] = Field(None, description="Destination folder for 'route' action")
    reply_text: Optional[str] = Field(None, description="Content for 'reply' action")

class EmailTriageObservation(Observation):
    inbox: List[Email] = Field(..., description="List of emails currently in the inbox waiting to be processed")
    folders: List[str] = Field(..., description="Available folders: ['sales', 'support', 'hr']")
    last_action_status: str = Field(..., description="Message indicating the result of the last action")
