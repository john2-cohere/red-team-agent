from typing import Optional

from pydantic import BaseModel

class Challenge(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = ""
    solved: bool = False

class DiscoveryChallenge(Challenge):
    url: str