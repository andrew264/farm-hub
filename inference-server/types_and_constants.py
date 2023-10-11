from typing import Literal, TypedDict, List, Optional

Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


Dialog = List[Message]

with open("./inference-server/sys_prompt.txt", "r") as f:
    DEFAULT_SYSTEM_PROMPT = f.read()

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
BOS, EOS = "<s>", "</s>"

WS_EOS = '//EOS//'
