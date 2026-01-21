from editor.highlighters.core.types import (
    Token, StateStack, TokenizeResult, StyleId, StackFrame
)
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer

STATE_DEFAULT = 0
STATE_TRIPLE_SINGLE = 1
STATE_TRIPLE_DOUBLE = 2

KEYWORDS: set[str] = {
    "if", "else", "elif", "for", "while", "def", "class", "return",
    "import", "from", "as", "try", "except", "finally", "with",
    "lambda", "yield", "raise", "pass", "break", "continue",
    "and", "or", "not", "in", "is", "None", "True", "False",
    "async", "await"
}

OPERATORS: set[str] = {
    "+", "-", "*", "/", "//", "**", "%", "@",
    "=", "==", "!=", "<", ">", "<=", ">=", "<>",
    "&", "|", "^", "~", "<<", ">>",
    "+=", "-=", "*=", "/=", "//=", "**=", "%=", "@=",
    "&=", "|=", "^=", "<<=", ">>=",
    "->", ":="
}

PUNCTUATION: set[str] = {"(", ")", "[", "]", "{", "}", ":", ",", ".", ";"}


class PythonTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "python"

    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        tokens: list[Token] = []
        i = 0
        n = len(line)

        current_sub_state = STATE_DEFAULT
        if state_stack:
            top_frame = state_stack[-1]
            if top_frame.lang_id == "python":
                current_sub_state = top_frame.sub_state

        if current_sub_state in (STATE_TRIPLE_SINGLE, STATE_TRIPLE_DOUBLE):
            delimiter = "'''" if current_sub_state == STATE_TRIPLE_SINGLE else '"""'
            start = 0
            while i < n:
                if line[i] == '\\' and i + 1 < n:
                    i += 2
                    continue
                if line[i:i+3] == delimiter:
                    i += 3
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.STRING))
                    state_stack = state_stack[:-1]
                    current_sub_state = STATE_DEFAULT
                    break
                i += 1
            else:
                tokens.append(Token(start=start, length=n - start, style_id=StyleId.STRING))
                return TokenizeResult(tokens=tokens, final_stack=state_stack)

        while i < n:
            ch = line[i]

            if ch in ' \t\r\n':
                i += 1
                continue

            if ch == '#':
                tokens.append(Token(start=i, length=n - i, style_id=StyleId.COMMENT))
                break

            if ch == '@':
                start = i
                i += 1
                while i < n and (line[i].isalnum() or line[i] == '_' or line[i] == '.'):
                    i += 1
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.IDENTIFIER))
                continue

            if ch in ('"', "'"):
                start = i
                if line[i:i+3] in ('"""', "'''"):
                    delimiter = line[i:i+3]
                    sub_state = STATE_TRIPLE_DOUBLE if delimiter == '"""' else STATE_TRIPLE_SINGLE
                    i += 3
                    while i < n:
                        if line[i] == '\\' and i + 1 < n:
                            i += 2
                            continue
                        if line[i:i+3] == delimiter:
                            i += 3
                            tokens.append(Token(start=start, length=i - start, style_id=StyleId.STRING))
                            break
                        i += 1
                    else:
                        tokens.append(Token(start=start, length=n - start, style_id=StyleId.STRING))
                        new_frame = StackFrame(lang_id="python", sub_state=sub_state, end_condition=None)
                        state_stack = state_stack + (new_frame,)
                    continue
                else:
                    quote = ch
                    i += 1
                    while i < n:
                        if line[i] == '\\' and i + 1 < n:
                            i += 2
                        elif line[i] == quote:
                            i += 1
                            break
                        else:
                            i += 1
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.STRING))
                    continue

            if ch.isdigit() or (ch == '.' and i + 1 < n and line[i + 1].isdigit()):
                start = i
                if line[i:i+2] in ('0x', '0X'):
                    i += 2
                    while i < n and (line[i].isdigit() or line[i] in 'abcdefABCDEF_'):
                        i += 1
                elif line[i:i+2] in ('0b', '0B'):
                    i += 2
                    while i < n and line[i] in '01_':
                        i += 1
                elif line[i:i+2] in ('0o', '0O'):
                    i += 2
                    while i < n and line[i] in '01234567_':
                        i += 1
                else:
                    while i < n and (line[i].isdigit() or line[i] == '_'):
                        i += 1
                    if i < n and line[i] == '.':
                        i += 1
                        while i < n and (line[i].isdigit() or line[i] == '_'):
                            i += 1
                    if i < n and line[i] in 'eE':
                        i += 1
                        if i < n and line[i] in '+-':
                            i += 1
                        while i < n and (line[i].isdigit() or line[i] == '_'):
                            i += 1
                    if i < n and line[i] in 'jJ':
                        i += 1
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.NUMBER))
                continue

            if ch.isalpha() or ch == '_':
                start = i
                while i < n and (line[i].isalnum() or line[i] == '_'):
                    i += 1
                word = line[start:i]
                if word in KEYWORDS:
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.KEYWORD))
                else:
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.IDENTIFIER))
                continue

            if i + 2 <= n and line[i:i+3] in OPERATORS:
                tokens.append(Token(start=i, length=3, style_id=StyleId.OPERATOR))
                i += 3
                continue
            if i + 1 < n and line[i:i+2] in OPERATORS:
                tokens.append(Token(start=i, length=2, style_id=StyleId.OPERATOR))
                i += 2
                continue
            if ch in OPERATORS:
                tokens.append(Token(start=i, length=1, style_id=StyleId.OPERATOR))
                i += 1
                continue

            if ch in PUNCTUATION:
                tokens.append(Token(start=i, length=1, style_id=StyleId.PUNCTUATION))
                i += 1
                continue

            i += 1

        return TokenizeResult(tokens=tokens, final_stack=state_stack)
