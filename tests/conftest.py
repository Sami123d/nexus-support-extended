import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DEEPSEEK_API_KEY", "test-primary-key")
os.environ.setdefault("API_KEY", "test-api-key")


@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_customers.db")
