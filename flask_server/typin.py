from enum import Enum
from typing import TypedDict, Optional, List

with open("sys_prompt.txt", "r") as f:
    DEFAULT_SYSTEM_PROMPT = f.read()

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
BOS, EOS = "<s>", "</s>"
WS_EOS = '//EOS//'


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(TypedDict):
    role: Role
    content: str


class Dialog:
    def __init__(self):
        self.messages: List[Message] = []
        system_message = {"role": Role.SYSTEM, "content": DEFAULT_SYSTEM_PROMPT, }
        self.messages.append(system_message)

    @property
    def system_message(self) -> Optional[Message]:
        return self.messages[0]

    def add_user_message(self, content: str):
        self.messages.append({"role": Role.USER, "content": content})

    def add_assistant_message(self, content: str):
        self.messages.append({"role": Role.ASSISTANT, "content": content})

    def reset(self):
        self.messages = []
        system_message = {"role": Role.SYSTEM, "content": DEFAULT_SYSTEM_PROMPT, }
        self.messages.append(system_message)

    def get_tokens(self) -> str:
        dialog = self.messages
        if dialog[0]["role"] == Role.SYSTEM:
            dialog = [
                         {
                             "role": dialog[1]["role"],
                             "content":
                                 B_SYS + dialog[0]["content"] + E_SYS + dialog[1]["content"],
                         }
                     ] + dialog[2:]
        assert all([msg["role"] == Role.USER for msg in dialog[::2]]) and all(
            [msg["role"] == Role.ASSISTANT for msg in dialog[1::2]]
        ), (
            "model only supports 'system', 'user' and 'assistant' roles, "
            "starting with 'system', then 'user' and alternating (u/a/u/a/u...)"
        )
        dialog_tokens = sum(
            [
                [f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()} {EOS}"]
                for prompt, answer in zip(dialog[::2], dialog[1::2], )
            ],
            [],
        )
        assert (
                dialog[-1]["role"] == Role.USER
        ), f"Last message must be from user, got {dialog[-1]['role']}"
        dialog_tokens += f"{BOS}{B_INST} {(dialog[-1]['content']).strip()} {E_INST}",
        return ''.join(dialog_tokens)
