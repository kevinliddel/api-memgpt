from pydantic import BaseModel


class Session(BaseModel):
    session: str


class Message(BaseModel):
    prompt: str
