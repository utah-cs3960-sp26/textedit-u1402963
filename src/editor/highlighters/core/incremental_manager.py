"""Manages per-line state caching for incremental highlighting."""


class IncrementalManager:
    """Manages per-line state caching and determines when to stop propagating rehighlighting."""

    def __init__(self) -> None:
        """Initialize empty state."""
        self._line_states: list[int] = []
        self._line_hashes: list[int] = []

    def set_line_count(self, count: int) -> None:
        """Resize internal arrays, fill new entries with -1."""
        current_count = len(self._line_states)
        if count > current_count:
            self._line_states.extend([-1] * (count - current_count))
            self._line_hashes.extend([-1] * (count - current_count))
        elif count < current_count:
            self._line_states = self._line_states[:count]
            self._line_hashes = self._line_hashes[:count]

    def update_line(self, index: int, text: str, final_state_id: int) -> bool:
        """Update cache for line at index.

        Returns True if state changed (requiring propagation to next lines).
        Returns False if state unchanged (early exit signal).
        """
        if index < 0 or index >= len(self._line_states):
            return True

        text_hash = hash(text)
        old_state = self._line_states[index]
        old_hash = self._line_hashes[index]

        self._line_states[index] = final_state_id
        self._line_hashes[index] = text_hash

        return old_state != final_state_id or old_hash != text_hash

    def get_initial_state_id(self, index: int) -> int:
        """Return final state of previous line (or -1 for line 0).

        Used to get the starting state for tokenizing a line.
        """
        if index <= 0:
            return -1
        if index - 1 >= len(self._line_states):
            return -1
        return self._line_states[index - 1]

    def invalidate_from(self, index: int) -> None:
        """Mark all lines from index onwards as needing re-tokenization.

        Sets state IDs to -1 from index onwards.
        """
        for i in range(index, len(self._line_states)):
            self._line_states[i] = -1

    def clear(self) -> None:
        """Reset all state."""
        self._line_states.clear()
        self._line_hashes.clear()
