import pytest
from orchestrator import pipeline

@pytest.fixture(autouse=True)
def mock_engines_for_tests(monkeypatch):
    """By default, normal tests run with mocks unless they explicitly ask for real engines.
    
    This preserves the hermetic nature of the test suite and prevents tests that
    expect mock output from failing now that production defaults to real engines.
    Tests can still override this by mutating pipeline.REAL_ENGINES during execution,
    which will operate on the empty set provided here and revert afterwards.
    """
    monkeypatch.setattr(pipeline, "REAL_ENGINES", set())
