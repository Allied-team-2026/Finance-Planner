"""Empty on purpose.

Without a conftest.py at the repo root, pytest puts `tests/` on the import path
and not the repo root, so `tests/conftest.py`'s `from orchestrator import pipeline`
fails with ModuleNotFoundError and the whole suite refuses to start. pytest adds
the directory of the topmost conftest to the import path, so this file existing is
the entire fix. `python -m pytest` also works, but only because it happens to add
the current directory - this way plain `pytest` works for everyone.
"""
