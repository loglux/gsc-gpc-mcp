from unittest.mock import MagicMock

import pytest

from gsc import tools


@pytest.fixture
def mock_service():
    return MagicMock()


def test_get_performance_default_dimensions(mock_service):
    expected = {"rows": [{"keys": ["python tutorial"], "clicks": 100}]}
    mock_service.searchanalytics().query().execute.return_value = expected

    result = tools.get_performance(mock_service, "https://example.com/", "2024-01-01", "2024-01-31")

    mock_service.searchanalytics().query.assert_called_with(
        siteUrl="https://example.com/",
        body={
            "startDate": "2024-01-01",
            "endDate": "2024-01-31",
            "dimensions": ["query"],
            "rowLimit": 1000,
        },
    )
    assert result == expected


def test_get_performance_custom_dimensions(mock_service):
    mock_service.searchanalytics().query().execute.return_value = {}
    tools.get_performance(
        mock_service,
        "https://example.com/",
        "2024-01-01",
        "2024-01-31",
        dimensions=["page", "country"],
        row_limit=500,
    )
    call_body = mock_service.searchanalytics().query.call_args[1]["body"]
    assert call_body["dimensions"] == ["page", "country"]
    assert call_body["rowLimit"] == 500


def test_inspect_url(mock_service):
    expected = {
        "inspectionResult": {"indexStatusResult": {"coverageState": "Submitted and indexed"}}
    }
    mock_service.urlInspection().index().inspect().execute.return_value = expected

    result = tools.inspect_url(mock_service, "https://example.com/", "https://example.com/page")
    assert result == expected


def test_list_sitemaps(mock_service):
    expected = {"sitemap": [{"path": "https://example.com/sitemap.xml"}]}
    mock_service.sitemaps().list().execute.return_value = expected

    result = tools.list_sitemaps(mock_service, "https://example.com/")
    assert result == expected


def test_submit_sitemap(mock_service):
    result = tools.submit_sitemap(
        mock_service, "https://example.com/", "https://example.com/sitemap.xml"
    )
    assert result["status"] == "submitted"
    assert "sitemap.xml" in result["sitemap"]


def test_list_sites(mock_service):
    expected = {"siteEntry": [{"siteUrl": "https://example.com/"}]}
    mock_service.sites().list().execute.return_value = expected

    result = tools.list_sites(mock_service)
    assert result == expected
