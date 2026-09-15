from pydantic import BaseModel

class PromptObject(BaseModel):
    content: str
    id: str
    role: str

