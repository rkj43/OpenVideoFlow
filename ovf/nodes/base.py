import time
from abc import ABC, abstractmethod

from rich.console import Console

from ovf.context import Context
from ovf.result import TaskResult

console = Console()


class Node(ABC):
    name: str = "node"

    def run(self, context: Context) -> Context:
        console.rule(f"[bold cyan]{self.name}")
        start = time.monotonic()
        try:
            context = self._run(context)
            duration = time.monotonic() - start
            console.print(f"[green]✓ {self.name}[/green] completed in {duration:.1f}s")
        except Exception as exc:
            duration = time.monotonic() - start
            console.print(f"[red]✗ {self.name}[/red] failed after {duration:.1f}s: {exc}")
            raise
        return context

    @abstractmethod
    def _run(self, context: Context) -> Context:
        raise NotImplementedError
