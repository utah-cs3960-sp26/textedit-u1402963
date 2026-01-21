from .types import StateStack


class StateStackPool:
    _instance: "StateStackPool | None" = None

    def __new__(cls) -> "StateStackPool":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._stack_to_id: dict[StateStack, int] = {}
            cls._instance._id_to_stack: dict[int, StateStack] = {}
            cls._instance._next_id: int = 0
        return cls._instance

    def intern(self, stack: StateStack) -> int:
        if stack in self._stack_to_id:
            return self._stack_to_id[stack]

        state_id = self._next_id
        self._next_id += 1
        self._stack_to_id[stack] = state_id
        self._id_to_stack[state_id] = stack
        return state_id

    def get(self, state_id: int) -> StateStack:
        if state_id == -1:
            return ()
        return self._id_to_stack.get(state_id, ())

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
