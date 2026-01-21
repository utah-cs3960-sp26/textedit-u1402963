from editor.highlighters.core.types import (
    Token, StateStack, TokenizeResult, StyleId, StackFrame
)
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer

STATE_DEFAULT = 0
STATE_BLOCK_COMMENT = 1
STATE_TEMPLATE_STRING = 2

KEYWORDS: set[str] = {
    "break", "case", "catch", "class", "const", "continue", "debugger",
    "default", "delete", "do", "else", "export", "extends", "finally",
    "for", "function", "if", "import", "in", "instanceof", "let", "new",
    "return", "super", "switch", "this", "throw", "try", "typeof", "var",
    "void", "while", "with", "yield", "async", "await", "of",
    "true", "false", "null", "undefined"
}

OPERATORS: set[str] = {
    "+", "-", "*", "/", "%", "**",
    "=", "==", "===", "!=", "!==", "<", ">", "<=", ">=",
    "&", "|", "^", "~", "<<", ">>", ">>>",
    "&&", "||", "??", "!",
    "+=", "-=", "*=", "/=", "%=", "**=",
    "&=", "|=", "^=", "<<=", ">>=", ">>>=",
    "&&=", "||=", "??=",
    "++", "--",
    "=>", "?", ":"
}

PUNCTUATION: set[str] = {"(", ")", "[", "]", "{", "}", ",", ".", ";"}


class JavaScriptTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "javascript"

    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        tokens: list[Token] = []
        i = 0
        n = len(line)

        current_sub_state = STATE_DEFAULT
        if state_stack:
            top_frame = state_stack[-1]
            if top_frame.lang_id == "javascript":
                current_sub_state = top_frame.sub_state

        if current_sub_state == STATE_BLOCK_COMMENT:
            i = self._continue_block_comment(line, i, tokens, state_stack)
            if i >= n:
                return TokenizeResult(tokens=tokens, final_stack=state_stack)
            state_stack = state_stack[:-1]

        if current_sub_state == STATE_TEMPLATE_STRING:
            i, state_stack = self._continue_template_string(line, i, tokens, state_stack)
            if i >= n:
                return TokenizeResult(tokens=tokens, final_stack=state_stack)

        while i < n:
            ch = line[i]

            if ch in ' \t\r\n':
                i += 1
                continue

            if line[i:i+2] == '//':
                tokens.append(Token(start=i, length=n - i, style_id=StyleId.COMMENT))
                break

            if line[i:i+2] == '/*':
                start = i
                i += 2
                while i < n:
                    if line[i:i+2] == '*/':
                        i += 2
                        tokens.append(Token(start=start, length=i - start, style_id=StyleId.COMMENT))
                        break
                    i += 1
                else:
                    tokens.append(Token(start=start, length=n - start, style_id=StyleId.COMMENT))
                    new_frame = StackFrame(lang_id="javascript", sub_state=STATE_BLOCK_COMMENT, end_condition=None)
                    state_stack = state_stack + (new_frame,)
                continue

            if ch == '`':
                start = i
                i += 1
                while i < n:
                    if line[i] == '\\' and i + 1 < n:
                        i += 2
                        continue
                    if line[i] == '`':
                        i += 1
                        tokens.append(Token(start=start, length=i - start, style_id=StyleId.STRING))
                        break
                    i += 1
                else:
                    tokens.append(Token(start=start, length=n - start, style_id=StyleId.STRING))
                    new_frame = StackFrame(lang_id="javascript", sub_state=STATE_TEMPLATE_STRING, end_condition=None)
                    state_stack = state_stack + (new_frame,)
                continue

            if ch in ('"', "'"):
                start = i
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

            if ch == '/' and self._can_start_regex(tokens):
                result = self._try_parse_regex(line, i)
                if result is not None:
                    length = result
                    tokens.append(Token(start=i, length=length, style_id=StyleId.STRING))
                    i += length
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
                if i < n and line[i] == 'n':
                    i += 1
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.NUMBER))
                continue

            if ch.isalpha() or ch == '_' or ch == '$':
                start = i
                while i < n and (line[i].isalnum() or line[i] == '_' or line[i] == '$'):
                    i += 1
                word = line[start:i]
                if word in KEYWORDS:
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.KEYWORD))
                else:
                    tokens.append(Token(start=start, length=i - start, style_id=StyleId.IDENTIFIER))
                continue

            if i + 3 <= n and line[i:i+4] in OPERATORS:
                tokens.append(Token(start=i, length=4, style_id=StyleId.OPERATOR))
                i += 4
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

    def _continue_block_comment(self, line: str, i: int, tokens: list[Token], state_stack: StateStack) -> int:
        n = len(line)
        start = i
        while i < n:
            if line[i:i+2] == '*/':
                i += 2
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.COMMENT))
                return i
            i += 1
        tokens.append(Token(start=start, length=n - start, style_id=StyleId.COMMENT))
        return n

    def _continue_template_string(
        self, line: str, i: int, tokens: list[Token], state_stack: StateStack
    ) -> tuple[int, StateStack]:
        n = len(line)
        start = i
        while i < n:
            if line[i] == '\\' and i + 1 < n:
                i += 2
                continue
            if line[i] == '`':
                i += 1
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.STRING))
                state_stack = state_stack[:-1]
                return i, state_stack
            i += 1
        tokens.append(Token(start=start, length=n - start, style_id=StyleId.STRING))
        return n, state_stack

    def _can_start_regex(self, tokens: list[Token]) -> bool:
        if not tokens:
            return True
        last_token = tokens[-1]
        if last_token.style_id in (StyleId.OPERATOR, StyleId.PUNCTUATION, StyleId.KEYWORD):
            return True
        return False

    def _try_parse_regex(self, line: str, i: int) -> int | None:
        n = len(line)
        if i >= n or line[i] != '/':
            return None
        j = i + 1
        if j >= n or line[j] in ('/', '*'):
            return None
        in_class = False
        while j < n:
            ch = line[j]
            if ch == '\\' and j + 1 < n:
                j += 2
                continue
            if ch == '[':
                in_class = True
            elif ch == ']':
                in_class = False
            elif ch == '/' and not in_class:
                j += 1
                while j < n and line[j].isalpha():
                    j += 1
                return j - i
            elif ch in '\r\n':
                return None
            j += 1
        return None
