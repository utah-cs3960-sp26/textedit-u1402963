from enum import IntEnum
from typing import NamedTuple


class Token(NamedTuple):
    start: int
    length: int
    style_id: int


class StyleId(IntEnum):
    PLAIN = 0
    KEYWORD = 1
    STRING = 2
    COMMENT = 3
    NUMBER = 4
    OPERATOR = 5
    TAG = 6
    ATTR_NAME = 7
    ATTR_VALUE = 8
    PUNCTUATION = 9
    IDENTIFIER = 10
    EMBEDDED = 11


class StackFrame(NamedTuple):
    lang_id: str
    sub_state: int
    end_condition: str | None


StateStack = tuple[StackFrame, ...]


class TokenizeResult(NamedTuple):
    tokens: list[Token]
    final_stack: StateStack
