import pytest
import os
from pathlib import Path

@pytest.fixture
def fixtures_dir():
    return Path(os.path.dirname(__file__)) / "fixtures"
