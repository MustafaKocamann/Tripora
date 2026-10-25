from agent import run


def test_entry_point_accepts_claim_and_thread() -> None:
    assert run("CLM-1001", "thread-1") == {
        "claim_id": "CLM-1001",
        "thread_id": "thread-1",
    }
