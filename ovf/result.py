from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TaskResult:
    status: str  # "success" | "error"
    output: Any
    metadata: dict = field(default_factory=dict)
    duration: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.status == "success"
