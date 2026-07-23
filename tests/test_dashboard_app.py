import importlib


def test_dashboard_module_imports_without_running():
    # Importing must not execute Streamlit calls (they live inside render()).
    mod = importlib.import_module("dashboard.app")
    assert hasattr(mod, "render")
