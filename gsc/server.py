from fastmcp import FastMCP
from shared.auth import build_gsc_service
from gsc import tools

mcp = FastMCP("google-search-console")
_service = None


def _get_service():
    global _service
    if _service is None:
        _service = build_gsc_service()
    return _service


@mcp.tool()
def gsc_get_performance(
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    row_limit: int = 1000,
) -> dict:
    """Fetch Search Console performance data: queries, clicks, impressions, CTR, position.

    Args:
        site_url: Property URL, e.g. "https://example.com/" or "sc-domain:example.com"
        start_date: ISO date, e.g. "2024-01-01"
        end_date: ISO date, e.g. "2024-01-31"
        dimensions: List of dimensions to group by: query, page, country, device, date
        row_limit: Max rows to return (default 1000, max 25000)
    """
    return tools.get_performance(_get_service(), site_url, start_date, end_date, dimensions, row_limit)


@mcp.tool()
def gsc_inspect_url(site_url: str, url: str) -> dict:
    """Check indexing status of a specific URL in Google Search Console.

    Args:
        site_url: Property URL the page belongs to
        url: The specific URL to inspect
    """
    return tools.inspect_url(_get_service(), site_url, url)


@mcp.tool()
def gsc_list_sitemaps(site_url: str) -> dict:
    """List all sitemaps submitted for a Search Console property.

    Args:
        site_url: Property URL, e.g. "https://example.com/"
    """
    return tools.list_sitemaps(_get_service(), site_url)


@mcp.tool()
def gsc_submit_sitemap(site_url: str, sitemap_url: str) -> dict:
    """Submit a sitemap to Google Search Console.

    Args:
        site_url: Property URL
        sitemap_url: Full URL of the sitemap to submit
    """
    return tools.submit_sitemap(_get_service(), site_url, sitemap_url)


@mcp.tool()
def gsc_list_sites() -> dict:
    """List all Search Console properties accessible to the service account."""
    return tools.list_sites(_get_service())


def main():
    mcp.run()


if __name__ == "__main__":
    main()
