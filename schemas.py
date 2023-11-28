from pydantic import BaseModel


class Session(BaseModel):
    session: str


class Message(BaseModel):
    prompt: str


class RecallMemoryStats(BaseModel):
    total_messages: int
    system: int
    user: int
    assistant: int
    function: int
    other: int
