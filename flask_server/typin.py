from typing import TypedDict, Optional, Literal, List

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


Dialog = List[Message]


class RenderObj(TypedDict):
    content: str
    image_base64: Optional[str]
    lang: str
    sender: str

