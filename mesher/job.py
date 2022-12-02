import attrs
import enum
from pathlib import Path

class State(enum.Enum):
    running = enum.auto()
    error = enum.auto()
    success = enum.auto()
    
@attrs.frozen
class Job:
    status: State
    outfile: Path

    
    def set_finished(self):
        return attrs.evolve(self, status = State.success)

    def set_errored(self):
        return attrs.evolve(self, status = State.error)

    @classmethod
    def new_running(cls, path: Path):
        return cls(State.running, path)