import re

from editor.highlighters.core.types import (
    Token,
    StateStack,
    TokenizeResult,
    StyleId,
    StackFrame,
)
from editor.highlighters.tokenizers.base_tokenizer import BaseTokenizer

STATE_DEFAULT = 0
STATE_CODE_BLOCK = 1


class MarkdownTokenizer(BaseTokenizer):
    FENCE_PATTERN = re.compile(r'^(`{3,})(\w*)$')
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s')
    LIST_PATTERN = re.compile(r'^(\s*)([-*]|\d+\.)\s')
    BLOCKQUOTE_PATTERN = re.compile(r'^(>\s*)+')

    def get_lang_id(self) -> str:
        return "markdown"

    def _push_state(
        self,
        stack: StateStack,
        lang_id: str,
        sub_state: int,
        end_condition: str | None,
    ) -> StateStack:
        return stack + (StackFrame(lang_id, sub_state, end_condition),)

    def _pop_state(self, stack: StateStack) -> StateStack:
        if len(stack) > 1:
            return stack[:-1]
        return stack

    def _get_current_frame(self, stack: StateStack) -> StackFrame:
        return stack[-1] if stack else StackFrame("markdown", STATE_DEFAULT, None)

    def tokenize_line(self, line: str, state_stack: StateStack) -> TokenizeResult:
        if not state_stack:
            state_stack = (StackFrame("markdown", STATE_DEFAULT, None),)

        tokens: list[Token] = []
        current_frame = self._get_current_frame(state_stack)

        if current_frame.sub_state == STATE_CODE_BLOCK:
            return self._tokenize_in_code_block(line, state_stack, current_frame)

        return self._tokenize_default(line, state_stack)

    def _tokenize_in_code_block(
        self,
        line: str,
        state_stack: StateStack,
        current_frame: StackFrame,
    ) -> TokenizeResult:
        tokens: list[Token] = []
        stripped = line.rstrip()

        fence_match = self.FENCE_PATTERN.match(stripped)
        if fence_match:
            fence = fence_match.group(1)
            if current_frame.end_condition and fence.startswith(
                current_frame.end_condition
            ):
                tokens.append(
                    Token(start=0, length=len(stripped), style_id=StyleId.PUNCTUATION)
                )
                state_stack = self._pop_state(state_stack)
                return TokenizeResult(tokens=tokens, final_stack=state_stack)

        if line:
            tokens.append(Token(start=0, length=len(line), style_id=StyleId.EMBEDDED))

        return TokenizeResult(tokens=tokens, final_stack=state_stack)

    def _tokenize_default(
        self, line: str, state_stack: StateStack
    ) -> TokenizeResult:
        tokens: list[Token] = []
        n = len(line)
        stripped = line.rstrip()

        fence_match = self.FENCE_PATTERN.match(stripped)
        if fence_match:
            fence = fence_match.group(1)
            language = fence_match.group(2) or "code"
            tokens.append(
                Token(start=0, length=len(stripped), style_id=StyleId.PUNCTUATION)
            )
            state_stack = self._push_state(state_stack, language, STATE_CODE_BLOCK, fence)
            return TokenizeResult(tokens=tokens, final_stack=state_stack)

        header_match = self.HEADER_PATTERN.match(line)
        if header_match:
            tokens.append(Token(start=0, length=n, style_id=StyleId.KEYWORD))
            return TokenizeResult(tokens=tokens, final_stack=state_stack)

        blockquote_match = self.BLOCKQUOTE_PATTERN.match(line)
        if blockquote_match:
            tokens.append(Token(start=0, length=n, style_id=StyleId.COMMENT))
            return TokenizeResult(tokens=tokens, final_stack=state_stack)

        list_match = self.LIST_PATTERN.match(line)
        if list_match:
            marker_end = list_match.end()
            tokens.append(
                Token(start=0, length=marker_end, style_id=StyleId.PUNCTUATION)
            )
            if marker_end < n:
                inline_tokens = self._tokenize_inline(line, marker_end, n)
                tokens.extend(inline_tokens)
            return TokenizeResult(tokens=tokens, final_stack=state_stack)

        inline_tokens = self._tokenize_inline(line, 0, n)
        tokens.extend(inline_tokens)

        return TokenizeResult(tokens=tokens, final_stack=state_stack)

    def _tokenize_inline(
        self, line: str, start: int, end: int
    ) -> list[Token]:
        tokens: list[Token] = []
        i = start

        while i < end:
            ch = line[i]

            if ch == '`':
                code_end = line.find('`', i + 1)
                if code_end != -1:
                    length = code_end - i + 1
                    tokens.append(Token(start=i, length=length, style_id=StyleId.STRING))
                    i = code_end + 1
                    continue
                i += 1
                continue

            if ch == '*' and i + 1 < end and line[i + 1] == '*':
                close = line.find('**', i + 2)
                if close != -1:
                    length = close - i + 2
                    tokens.append(Token(start=i, length=length, style_id=StyleId.KEYWORD))
                    i = close + 2
                    continue
                i += 1
                continue

            if ch == '_' and i + 1 < end and line[i + 1] == '_':
                close = line.find('__', i + 2)
                if close != -1:
                    length = close - i + 2
                    tokens.append(Token(start=i, length=length, style_id=StyleId.KEYWORD))
                    i = close + 2
                    continue
                i += 1
                continue

            if ch == '*' and i + 1 < end and line[i + 1] != '*':
                close = self._find_single_marker(line, i + 1, end, '*')
                if close != -1:
                    length = close - i + 1
                    tokens.append(Token(start=i, length=length, style_id=StyleId.COMMENT))
                    i = close + 1
                    continue
                i += 1
                continue

            if ch == '_' and i + 1 < end and line[i + 1] != '_':
                if i == start or not line[i - 1].isalnum():
                    close = self._find_single_marker(line, i + 1, end, '_')
                    if close != -1 and (close + 1 >= end or not line[close + 1].isalnum()):
                        length = close - i + 1
                        tokens.append(Token(start=i, length=length, style_id=StyleId.COMMENT))
                        i = close + 1
                        continue
                i += 1
                continue

            if ch == '[':
                result = self._parse_link(line, i, end)
                if result:
                    link_tokens, new_pos = result
                    tokens.extend(link_tokens)
                    i = new_pos
                    continue
                i += 1
                continue

            i += 1

        return tokens

    def _find_single_marker(
        self, line: str, start: int, end: int, marker: str
    ) -> int:
        i = start
        while i < end:
            if line[i] == marker:
                if marker == '*' and i + 1 < end and line[i + 1] == '*':
                    i += 2
                    continue
                if marker == '_' and i + 1 < end and line[i + 1] == '_':
                    i += 2
                    continue
                return i
            i += 1
        return -1

    def _parse_link(
        self, line: str, start: int, end: int
    ) -> tuple[list[Token], int] | None:
        if line[start] != '[':
            return None

        bracket_close = line.find(']', start + 1)
        if bracket_close == -1 or bracket_close + 1 >= end:
            return None

        if line[bracket_close + 1] != '(':
            return None

        paren_close = line.find(')', bracket_close + 2)
        if paren_close == -1:
            return None

        tokens: list[Token] = []

        tokens.append(Token(start=start, length=1, style_id=StyleId.PUNCTUATION))

        text_start = start + 1
        text_length = bracket_close - text_start
        if text_length > 0:
            tokens.append(
                Token(start=text_start, length=text_length, style_id=StyleId.ATTR_NAME)
            )

        tokens.append(Token(start=bracket_close, length=1, style_id=StyleId.PUNCTUATION))
        tokens.append(Token(start=bracket_close + 1, length=1, style_id=StyleId.PUNCTUATION))

        url_start = bracket_close + 2
        url_length = paren_close - url_start
        if url_length > 0:
            tokens.append(
                Token(start=url_start, length=url_length, style_id=StyleId.STRING)
            )

        tokens.append(Token(start=paren_close, length=1, style_id=StyleId.PUNCTUATION))

        return tokens, paren_close + 1
