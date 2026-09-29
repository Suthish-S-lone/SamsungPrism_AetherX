# Prototype schema draft — NOT official Samsung schema.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Step(BaseModel):
    text: str

class Action(BaseModel):
    action_name: str
    description: str
    category: Literal["auto", "manual", "critical"]
    steps: List[Step]
    target_screen: str
    deeplink: Optional[str] = None

class Context(BaseModel):
    goal: str
    title: str
    score: float = Field(ge=0, le=1)
    actions: List[Action]

class TroubleshootRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)

class TroubleshootResponse(BaseModel):
    contexts: List[Context] = []
    fallback: Optional[str] = None
