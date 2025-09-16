from pitcrew.service import TaskRegistry, InMemoryScheduler

def test_task_submission_and_processing():
    reg = TaskRegistry()
    observed = {}

    def handler(payload):
        observed['value'] = payload.get('x')
        return True

    reg.register('demo', handler)
    sched = InMemoryScheduler(registry=reg)
    t = sched.submit('demo', {'x': 42})
    assert t.id == 1
    processed = sched.run_once()
    assert processed == 1
    assert observed['value'] == 42
    assert sched.pending() == []


def test_task_failure_retained():
    reg = TaskRegistry()

    def boom(_):
        raise RuntimeError('fail')

    reg.register('fail', boom)
    sched = InMemoryScheduler(registry=reg)
    sched.submit('fail')
    processed = sched.run_once()
    assert processed == 0
    assert len(sched.pending()) == 1
