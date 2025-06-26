import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app

import pytest

@pytest.fixture
def app():
    yield flask_app
