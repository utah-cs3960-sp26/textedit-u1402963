from editor.highlighters.core.types import Token, StateStack, TokenizeResult, StyleId
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer


class JsonTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "json"

    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        tokens: list[Token] = []
        i = 0
        n = len(line)
        expecting_value = False

        while i < n:
            ch = line[i]

            if ch in ' \t\r\n':
                i += 1
                continue

            if ch == '"':
                start = i
                i += 1
                while i < n:
                    if line[i] == '\\' and i + 1 < n:
                        i += 2
                    elif line[i] == '"':
                        i += 1
                        break
                    else:
                        i += 1
                string_content = line[start:i]

                j = i
                while j < n and line[j] in ' \t':
                    j += 1

                if j < n and line[j] == ':':
                    style = StyleId.ATTR_NAME
                    expecting_value = True
                else:
                    style = StyleId.STRING

                tokens.append(Token(start=start, length=len(string_content), style_id=style))
                continue

            if ch in '{}[]:,':
                tokens.append(Token(start=i, length=1, style_id=StyleId.PUNCTUATION))
                if ch == ':':
                    expecting_value = True
                elif ch in ',{}[]':
                    expecting_value = False
                i += 1
                continue

            if ch == '-' or ch.isdigit():
                start = i
                if ch == '-':
                    i += 1
                while i < n and line[i].isdigit():
                    i += 1
                if i < n and line[i] == '.':
                    i += 1
                    while i < n and line[i].isdigit():
                        i += 1
                if i < n and line[i] in 'eE':
                    i += 1
                    if i < n and line[i] in '+-':
                        i += 1
                    while i < n and line[i].isdigit():
                        i += 1
                tokens.append(Token(start=start, length=i - start, style_id=StyleId.NUMBER))
                expecting_value = False
                continue

            if line[i:i+4] == 'true':
                tokens.append(Token(start=i, length=4, style_id=StyleId.KEYWORD))
                i += 4
                expecting_value = False
                continue

            if line[i:i+5] == 'false':
                tokens.append(Token(start=i, length=5, style_id=StyleId.KEYWORD))
                i += 5
                expecting_value = False
                continue

            if line[i:i+4] == 'null':
                tokens.append(Token(start=i, length=4, style_id=StyleId.KEYWORD))
                i += 4
                expecting_value = False
                continue

            i += 1

        return TokenizeResult(tokens=tokens, final_stack=state_stack)
