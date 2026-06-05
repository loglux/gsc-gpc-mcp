from unittest.mock import MagicMock, patch

import pytest

from shared import auth


def test_load_credentials_missing_file():
    with pytest.raises(FileNotFoundError, match="Service account key not found"):
        auth.load_credentials("nonexistent.json", auth.GSC_SCOPES)


def test_load_credentials_success(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "CREDENTIALS_DIR", tmp_path)
    fake_key = tmp_path / "test-key.json"
    fake_key.write_text("{}")

    with patch("shared.auth.service_account.Credentials.from_service_account_file") as mock_creds:
        mock_creds.return_value = MagicMock()
        result = auth.load_credentials("test-key.json", auth.GSC_SCOPES)

    mock_creds.assert_called_once_with(str(fake_key), scopes=auth.GSC_SCOPES)
    assert result is not None


def test_gsc_scopes_are_readonly():
    for scope in auth.GSC_SCOPES:
        assert "readonly" in scope or "webmasters" in scope


def test_gpc_scopes_include_androidpublisher():
    assert any("androidpublisher" in s for s in auth.GPC_SCOPES)
