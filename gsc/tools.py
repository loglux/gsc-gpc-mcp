from googleapiclient.discovery import Resource


def get_performance(
    service: Resource,
    site_url: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    row_limit: int = 1000,
) -> dict:
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions or ["query"],
        "rowLimit": row_limit,
    }
    return service.searchanalytics().query(siteUrl=site_url, body=body).execute()


def inspect_url(service: Resource, site_url: str, url: str) -> dict:
    return (
        service.urlInspection()
        .index()
        .inspect(body={"inspectionUrl": url, "siteUrl": site_url})
        .execute()
    )


def list_sitemaps(service: Resource, site_url: str) -> dict:
    return service.sitemaps().list(siteUrl=site_url).execute()


def submit_sitemap(service: Resource, site_url: str, sitemap_url: str) -> dict:
    service.sitemaps().submit(siteUrl=site_url, feedpath=sitemap_url).execute()
    return {"status": "submitted", "sitemap": sitemap_url}


def list_sites(service: Resource) -> dict:
    return service.sites().list().execute()
