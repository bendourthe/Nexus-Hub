from service import run_task


def test_run_task() -> None:
    assert run_task(3) == 7
