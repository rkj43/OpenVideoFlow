from rich.console import Console

from ovf.context import Context
from ovf.nodes.base import Node

console = Console()


class Pipeline:
    def __init__(self, *nodes: Node):
        self.nodes = list(nodes)

    def run(self, context: Context) -> Context:
        console.print(f"\n[bold]OpenVideoFlow[/bold] — {len(self.nodes)} node(s)\n")
        for node in self.nodes:
            context = node.run(context)
        console.print("\n[bold green]Pipeline complete.[/bold green]")
        if context.output_path:
            console.print(f"Output: [bold]{context.output_path}[/bold]\n")
        return context
