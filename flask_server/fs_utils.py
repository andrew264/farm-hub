from typin import Dialog

with open("sys_prompt.txt", "r") as f:
    DEFAULT_SYSTEM_PROMPT = f.read()

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
BOS, EOS = "<s>", "</s>"
WS_EOS = '//EOS//'


def get_tokens(dialog: Dialog) -> str:
    if dialog[0]["role"] == "system":
        dialog = [
                     {
                         "role": dialog[1]["role"],
                         "content": B_SYS
                                    + dialog[0]["content"]
                                    + E_SYS
                                    + dialog[1]["content"],
                     }
                 ] + dialog[2:]
    assert all([msg["role"] == "user" for msg in dialog[::2]]) and all(
        [msg["role"] == "assistant" for msg in dialog[1::2]]
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
            dialog[-1]["role"] == "user"
    ), f"Last message must be from user, got {dialog[-1]['role']}"
    dialog_tokens += f"{BOS}{B_INST} {(dialog[-1]['content']).strip()} {E_INST}",
    return ''.join(dialog_tokens)
