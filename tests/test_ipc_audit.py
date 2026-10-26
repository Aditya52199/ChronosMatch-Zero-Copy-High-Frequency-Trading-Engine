from chronosmatch.ipc_audit import run_audit


def test_small_cross_process_ipc_audit():
    run_audit(count=1000, capacity=64)