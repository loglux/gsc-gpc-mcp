import os

from fastmcp import FastMCP

from gpc import tools
from shared.auth import build_gpc_service

mcp = FastMCP("google-play-console")
_service = None


def _get_service():
    global _service
    if _service is None:
        _service = build_gpc_service()
    return _service


@mcp.tool()
def gpc_list_reviews(
    package_name: str,
    max_results: int = 100,
    translation_language: str | None = None,
) -> dict:
    """List user reviews for an app on Google Play.

    Args:
        package_name: App package name, e.g. "com.example.app"
        max_results: Max reviews to return (default 100)
        translation_language: ISO 639-1 language code to translate reviews into
    """
    return tools.list_reviews(_get_service(), package_name, max_results, translation_language)


@mcp.tool()
def gpc_get_review(package_name: str, review_id: str) -> dict:
    """Get a specific review by ID.

    Args:
        package_name: App package name
        review_id: Review identifier
    """
    return tools.get_review(_get_service(), package_name, review_id)


@mcp.tool()
def gpc_reply_to_review(package_name: str, review_id: str, reply_text: str) -> dict:
    """Post a reply to a user review on Google Play.

    Args:
        package_name: App package name
        review_id: Review identifier
        reply_text: Text of the developer reply
    """
    return tools.reply_to_review(_get_service(), package_name, review_id, reply_text)


@mcp.tool()
def gpc_get_release_tracks(package_name: str) -> dict:
    """Get all release tracks (production, beta, alpha, internal) with current versions.

    Args:
        package_name: App package name
    """
    edit = _get_service().edits().insert(packageName=package_name, body={}).execute()
    edit_id = edit["id"]
    try:
        result = tools.list_tracks(_get_service(), package_name, edit_id)
        return result
    finally:
        _get_service().edits().delete(packageName=package_name, editId=edit_id).execute()


@mcp.tool()
def gpc_get_bundles(package_name: str) -> list[dict]:
    """List uploaded AAB bundles for an app.

    Args:
        package_name: App package name
    """
    return tools.get_bundle_listing(_get_service(), package_name)


@mcp.tool()
def gpc_get_install_stats(
    package_name: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
) -> dict:
    """Fetch install/uninstall statistics from Google Play.

    Args:
        package_name: App package name
        start_date: ISO date, e.g. "2024-01-01"
        end_date: ISO date, e.g. "2024-01-31"
        dimensions: Group by: date, country, deviceRamBucket, etc.
        metrics: activeDeviceInstalls, deviceInstalls, deviceUninstalls, etc.
    """
    return tools.get_install_stats(
        _get_service(), package_name, start_date, end_date, dimensions, metrics
    )


def main():
    port = int(os.environ.get("PORT", 0))
    if port:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run()  # stdio — for local testing


if __name__ == "__main__":
    main()
