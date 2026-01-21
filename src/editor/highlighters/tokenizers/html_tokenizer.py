import re
from editor.highlighters.core.base_tokenizer import BaseTokenizer
from editor.highlighters.core.types import Token, StateStack, TokenizeResult, StyleId, StackFrame


class HtmlTokenizer(BaseTokenizer):
    """Tokenizer for HTML with JavaScript and CSS embedding support."""

    STATE_DEFAULT = 0
    STATE_IN_TAG = 1
    STATE_IN_SCRIPT = 2
    STATE_IN_STYLE = 3
    STATE_IN_COMMENT = 4

    TAG_NAME_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9-]*')
    ATTR_NAME_RE = re.compile(r'[a-zA-Z_:][a-zA-Z0-9_:\-\.]*')
    ENTITY_RE = re.compile(r'&[a-zA-Z]+;|&#[0-9]+;|&#x[0-9a-fA-F]+;')

    def get_lang_id(self) -> str:
        return "html"

    def tokenize_line(
        self, line: str, state_stack: StateStack
    ) -> TokenizeResult:
        tokens: list[Token] = []
        pos = 0
        length = len(line)

        if not state_stack:
            state_stack = (self._default_frame(),)

        frame = self._current_frame(state_stack)
        if frame is None:
            frame = self._default_frame()
            state_stack = (frame,)

        while pos < length:
            frame = self._current_frame(state_stack)
            if frame is None:
                frame = self._default_frame()
                state_stack = (frame,)

            if frame.lang_id == "javascript":
                pos, state_stack = self._tokenize_embedded(
                    line, pos, tokens, state_stack, "</script>"
                )
            elif frame.lang_id == "css":
                pos, state_stack = self._tokenize_embedded(
                    line, pos, tokens, state_stack, "</style>"
                )
            elif frame.sub_state == self.STATE_IN_COMMENT:
                pos, state_stack = self._tokenize_comment(line, pos, tokens, state_stack)
            elif frame.sub_state == self.STATE_IN_TAG:
                pos, state_stack = self._tokenize_in_tag(line, pos, tokens, state_stack)
            else:
                pos, state_stack = self._tokenize_default(line, pos, tokens, state_stack)

        return TokenizeResult(tokens=tokens, final_stack=state_stack)

    def _tokenize_default(
        self, line: str, pos: int, tokens: list[Token], stack: StateStack
    ) -> tuple[int, StateStack]:
        length = len(line)

        if line[pos:pos + 4] == '<!--':
            tokens.append(self._make_token(pos, 4, StyleId.COMMENT))
            pos += 4
            stack = self._update_sub_state(stack, self.STATE_IN_COMMENT)
            return pos, stack

        if line[pos] == '<':
            if pos + 1 < length and line[pos + 1] == '/':
                start = pos
                pos += 2
                match = self.TAG_NAME_RE.match(line, pos)
                if match:
                    tag_name = match.group(0)
                    pos = match.end()
                    tokens.append(self._make_token(start, pos - start, StyleId.TAG))
                else:
                    tokens.append(self._make_token(start, 2, StyleId.TAG))
                stack = self._update_sub_state(stack, self.STATE_IN_TAG)
                return pos, stack
            else:
                start = pos
                pos += 1
                match = self.TAG_NAME_RE.match(line, pos)
                if match:
                    tag_name = match.group(0).lower()
                    pos = match.end()
                    tokens.append(self._make_token(start, pos - start, StyleId.TAG))
                    if tag_name == "script":
                        stack = self._set_pending_embed(stack, "javascript")
                    elif tag_name == "style":
                        stack = self._set_pending_embed(stack, "css")
                else:
                    tokens.append(self._make_token(start, 1, StyleId.TAG))
                stack = self._update_sub_state(stack, self.STATE_IN_TAG)
                return pos, stack

        entity_match = self.ENTITY_RE.match(line, pos)
        if entity_match:
            tokens.append(self._make_token(pos, len(entity_match.group(0)), StyleId.KEYWORD))
            return entity_match.end(), stack

        pos += 1
        return pos, stack

    def _tokenize_in_tag(
        self, line: str, pos: int, tokens: list[Token], stack: StateStack
    ) -> tuple[int, StateStack]:
        length = len(line)

        while pos < length and line[pos] in ' \t\n\r':
            pos += 1

        if pos >= length:
            return pos, stack

        if line[pos:pos + 2] == '/>':
            tokens.append(self._make_token(pos, 2, StyleId.TAG))
            stack = self._clear_pending_embed(stack)
            stack = self._update_sub_state(stack, self.STATE_DEFAULT)
            return pos + 2, stack

        if line[pos] == '>':
            tokens.append(self._make_token(pos, 1, StyleId.TAG))
            pos += 1
            pending = self._get_pending_embed(stack)
            stack = self._clear_pending_embed(stack)
            stack = self._update_sub_state(stack, self.STATE_DEFAULT)
            if pending == "javascript":
                stack = self._push_state(stack, "javascript", self.STATE_DEFAULT, "</script>")
            elif pending == "css":
                stack = self._push_state(stack, "css", self.STATE_DEFAULT, "</style>")
            return pos, stack

        attr_match = self.ATTR_NAME_RE.match(line, pos)
        if attr_match:
            attr_end = attr_match.end()
            next_pos = attr_end
            while next_pos < length and line[next_pos] in ' \t':
                next_pos += 1
            if next_pos < length and line[next_pos] == '=':
                tokens.append(self._make_token(pos, attr_end - pos, StyleId.ATTR_NAME))
                pos = next_pos + 1
                while pos < length and line[pos] in ' \t':
                    pos += 1
                if pos < length and line[pos] in '"\'':
                    quote = line[pos]
                    start = pos
                    pos += 1
                    while pos < length and line[pos] != quote:
                        pos += 1
                    if pos < length:
                        pos += 1
                    tokens.append(self._make_token(start, pos - start, StyleId.ATTR_VALUE))
                return pos, stack
            else:
                tokens.append(self._make_token(pos, attr_end - pos, StyleId.ATTR_NAME))
                return attr_end, stack

        pos += 1
        return pos, stack

    def _tokenize_comment(
        self, line: str, pos: int, tokens: list[Token], stack: StateStack
    ) -> tuple[int, StateStack]:
        start = pos
        length = len(line)

        while pos < length:
            if line[pos:pos + 3] == '-->':
                pos += 3
                tokens.append(self._make_token(start, pos - start, StyleId.COMMENT))
                stack = self._update_sub_state(stack, self.STATE_DEFAULT)
                return pos, stack
            pos += 1

        if pos > start:
            tokens.append(self._make_token(start, pos - start, StyleId.COMMENT))
        return pos, stack

    def _tokenize_embedded(
        self, line: str, pos: int, tokens: list[Token], stack: StateStack, end_tag: str
    ) -> tuple[int, StateStack]:
        start = pos
        length = len(line)
        end_tag_lower = end_tag.lower()
        end_tag_len = len(end_tag)

        while pos < length:
            if line[pos:pos + end_tag_len].lower() == end_tag_lower:
                if pos > start:
                    tokens.append(self._make_token(start, pos - start, StyleId.EMBEDDED))
                stack = self._pop_state(stack)
                tag_start = pos
                pos += end_tag_len
                match = self.TAG_NAME_RE.match(line, tag_start + 2)
                if match:
                    tokens.append(self._make_token(tag_start, pos - tag_start, StyleId.TAG))
                else:
                    tokens.append(self._make_token(tag_start, pos - tag_start, StyleId.TAG))
                stack = self._update_sub_state(stack, self.STATE_IN_TAG)
                return pos, stack
            pos += 1

        if pos > start:
            tokens.append(self._make_token(start, pos - start, StyleId.EMBEDDED))
        return pos, stack

    def _update_sub_state(self, stack: StateStack, new_sub_state: int) -> StateStack:
        if not stack:
            return (StackFrame(lang_id=self.get_lang_id(), sub_state=new_sub_state, end_condition=None),)
        frame = stack[-1]
        new_frame = StackFrame(
            lang_id=frame.lang_id,
            sub_state=new_sub_state,
            end_condition=frame.end_condition
        )
        return stack[:-1] + (new_frame,)

    def _set_pending_embed(self, stack: StateStack, embed_type: str) -> StateStack:
        if not stack:
            return (StackFrame(lang_id=self.get_lang_id(), sub_state=self.STATE_IN_TAG, end_condition=f"pending:{embed_type}"),)
        frame = stack[-1]
        new_frame = StackFrame(
            lang_id=frame.lang_id,
            sub_state=frame.sub_state,
            end_condition=f"pending:{embed_type}"
        )
        return stack[:-1] + (new_frame,)

    def _get_pending_embed(self, stack: StateStack) -> str | None:
        if not stack:
            return None
        frame = stack[-1]
        if frame.end_condition and frame.end_condition.startswith("pending:"):
            return frame.end_condition[8:]
        return None

    def _clear_pending_embed(self, stack: StateStack) -> StateStack:
        if not stack:
            return stack
        frame = stack[-1]
        if frame.end_condition and frame.end_condition.startswith("pending:"):
            new_frame = StackFrame(
                lang_id=frame.lang_id,
                sub_state=frame.sub_state,
                end_condition=None
            )
            return stack[:-1] + (new_frame,)
        return stack
