import time
from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

from ovf.context import Context

console = Console()


class Node(ABC):
    name: str = "node"
    max_retries: int = 0
    retry_delay: float = 5.0

    def run(self, context: Context) -> Context:
        console.rule(f"[bold cyan]{self.name}")
        start = time.monotonic()
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                console.print(f"  [yellow]Retry {attempt}/{self.max_retries} after {self.retry_delay}s…[/yellow]")
                time.sleep(self.retry_delay)
            try:
                context = self._run(context)
                duration = time.monotonic() - start
                console.print(f"[green]✓ {self.name}[/green] completed in {duration:.1f}s")
                return context
            except Exception as exc:
                last_exc = exc
                duration = time.monotonic() - start
                console.print(f"[red]✗ {self.name}[/red] failed after {duration:.1f}s: {exc}")
                if attempt == self.max_retries:
                    raise
        raise last_exc  # unreachable but satisfies type checker

    @abstractmethod
    def _run(self, context: Context) -> Context:
        raise NotImplementedError
