
from pydantic import BaseModel

class PostRequest(BaseModel):
    topic: str
    tone: str
