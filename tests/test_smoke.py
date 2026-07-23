import agentwatch


def test_package_has_version():
    assert isinstance(agentwatch.__version__, str)
    assert agentwatch.__version__ != ""
