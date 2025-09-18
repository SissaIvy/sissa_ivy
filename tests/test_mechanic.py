from mechanic.actions import ActionRegistry, DEFAULT_REGISTRY, echo_action


def test_default_registry_echo():
    result = DEFAULT_REGISTRY.run("echo", {"foo": "bar"})
    assert result == {"echo": {"foo": "bar"}}


def test_custom_registry():
    reg = ActionRegistry()
    reg.register("double", lambda p: p["n"] * 2)
    assert reg.run("double", {"n": 7}) == 14
    names = reg.list().keys()
    assert "double" in names
