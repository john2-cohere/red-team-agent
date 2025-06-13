from typing import Optional, List

from pydantic import BaseModel

class Challenge(BaseModel):
    id: int
    key: str
    name: str
    description: Optional[str] = ""
    solved: bool = False

class DiscoveryChallenge(Challenge):
    url: str

class ExploitChallenge(Challenge):
    url: str
    prompt: str
    success_condition: Optional[str]

class DiscoveryChallengeURL(Challenge):
    url: str
    url_ids: List[int]