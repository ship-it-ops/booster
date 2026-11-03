import pytest

from teamdocs import create_app

TEST_PARTNER_KEY = "sk_test_FAKE-not-a-real-key"  # fake key for the partner stub


@pytest.fixture
def app(tmp_path):
    return create_app({"DATABASE": str(tmp_path / "test.db"), "SECRET_KEY": "test", "TESTING": True})
