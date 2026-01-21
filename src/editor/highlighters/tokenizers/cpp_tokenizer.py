from editor.highlighters.tokenizers.c_tokenizer import CTokenizer, KEYWORDS as C_KEYWORDS

CPP_KEYWORDS: set[str] = C_KEYWORDS | {
    "class", "namespace", "template", "public", "private", "protected",
    "virtual", "override", "new", "delete", "try", "catch", "throw",
    "nullptr", "bool", "true", "false", "const_cast", "dynamic_cast",
    "static_cast", "reinterpret_cast", "using", "typename", "explicit",
    "inline", "mutable", "friend", "operator", "this", "constexpr",
    "noexcept", "decltype", "alignas", "alignof", "thread_local",
    "static_assert"
}


class CppTokenizer(CTokenizer):
    def get_lang_id(self) -> str:
        return "cpp"

    def _get_keywords(self) -> set[str]:
        return CPP_KEYWORDS
