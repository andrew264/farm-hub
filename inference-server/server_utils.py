from types_and_constants import Dialog, BOS, EOS, B_INST, E_INST, B_SYS, E_SYS


def get_tokens(dialog: Dialog) -> str:
    if dialog[0]["role"] == "system":
        dialog = [
                     {
                         "role": dialog[1]["role"],
                         "content": B_SYS + dialog[0]["content"] + E_SYS + dialog[1]["content"],
                     }
                 ] + dialog[2:]

    dialog_tokens = sum(
        [
            [f"{BOS}{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()}{EOS}"]
            for prompt, answer in zip(dialog[::2], dialog[1::2], )
        ],
        [],
    )
    dialog_tokens += f"{BOS}{B_INST} {(dialog[-1]['content']).strip()} {E_INST}{EOS}",
    return ''.join(dialog_tokens)
