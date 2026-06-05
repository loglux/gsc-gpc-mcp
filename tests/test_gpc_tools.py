from unittest.mock import MagicMock, call
import pytest
from gpc import tools


@pytest.fixture
def mock_service():
    return MagicMock()


def test_list_reviews_default(mock_service):
    expected = {"reviews": [{"reviewId": "abc123", "comments": []}]}
    mock_service.reviews().list().execute.return_value = expected

    result = tools.list_reviews(mock_service, "com.example.app")

    mock_service.reviews().list.assert_called_with(packageName="com.example.app", maxResults=100)
    assert result == expected


def test_list_reviews_with_translation(mock_service):
    mock_service.reviews().list().execute.return_value = {}
    tools.list_reviews(mock_service, "com.example.app", max_results=50, translation_language="en")

    mock_service.reviews().list.assert_called_with(
        packageName="com.example.app", maxResults=50, translationLanguage="en"
    )


def test_get_review(mock_service):
    expected = {"reviewId": "abc123"}
    mock_service.reviews().get().execute.return_value = expected

    result = tools.get_review(mock_service, "com.example.app", "abc123")
    assert result == expected


def test_reply_to_review(mock_service):
    expected = {"result": {"replyText": "Thank you!"}}
    mock_service.reviews().reply().execute.return_value = expected

    result = tools.reply_to_review(mock_service, "com.example.app", "abc123", "Thank you!")
    assert result == expected


def test_get_bundle_listing_cleans_up_edit(mock_service):
    edit_response = {"id": "edit-123"}
    mock_service.edits().insert().execute.return_value = edit_response
    mock_service.edits().bundles().list().execute.return_value = {"bundles": [{"versionCode": 42}]}

    result = tools.get_bundle_listing(mock_service, "com.example.app")

    assert result == [{"versionCode": 42}]
    mock_service.edits().delete.assert_called_with(packageName="com.example.app", editId="edit-123")


def test_get_bundle_listing_cleans_up_on_error(mock_service):
    edit_response = {"id": "edit-456"}
    mock_service.edits().insert().execute.return_value = edit_response
    mock_service.edits().bundles().list().execute.side_effect = Exception("API error")

    with pytest.raises(Exception, match="API error"):
        tools.get_bundle_listing(mock_service, "com.example.app")

    mock_service.edits().delete.assert_called_with(packageName="com.example.app", editId="edit-456")
