import pytest

from ovf.context import Context
from ovf.nodes.base import Node
from ovf.storage import Storage


class _FailThenSucceedNode(Node):
    name = "flaky"
    max_retries = 2
    retry_delay = 0.0

    def __init__(self, fail_times: int):
        self.calls = 0
        self.fail_times = fail_times

    def _run(self, context: Context) -> Context:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError(f"Intentional failure #{self.calls}")
        return context


def _ctx(tmp_path):
    run_dir = Storage(tmp_path).new_run()
    return Context(prompt="test", run_dir=run_dir)


def test_succeeds_after_retries(tmp_path):
    node = _FailThenSucceedNode(fail_times=2)
    ctx = node.run(_ctx(tmp_path))
    assert node.calls == 3


def test_raises_after_max_retries(tmp_path):
    node = _FailThenSucceedNode(fail_times=5)
    with pytest.raises(RuntimeError, match="Intentional failure"):
        node.run(_ctx(tmp_path))
    assert node.calls == 3  # 1 attempt + 2 retries
