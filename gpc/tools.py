from googleapiclient.discovery import Resource


def get_app_details(service: Resource, package_name: str) -> dict:
    return service.edits().insert(packageName=package_name, body={}).execute()


def list_reviews(
    service: Resource,
    package_name: str,
    max_results: int = 100,
    translation_language: str | None = None,
) -> dict:
    params = {"packageName": package_name, "maxResults": max_results}
    if translation_language:
        params["translationLanguage"] = translation_language
    return service.reviews().list(**params).execute()


def get_review(service: Resource, package_name: str, review_id: str) -> dict:
    return service.reviews().get(packageName=package_name, reviewId=review_id).execute()


def reply_to_review(service: Resource, package_name: str, review_id: str, reply_text: str) -> dict:
    body = {"replyText": reply_text}
    return (
        service.reviews()
        .reply(packageName=package_name, reviewId=review_id, body=body)
        .execute()
    )


def list_tracks(service: Resource, package_name: str, edit_id: str) -> dict:
    return service.edits().tracks().list(packageName=package_name, editId=edit_id).execute()


def get_track(service: Resource, package_name: str, edit_id: str, track: str) -> dict:
    return (
        service.edits()
        .tracks()
        .get(packageName=package_name, editId=edit_id, track=track)
        .execute()
    )


def get_bundle_listing(service: Resource, package_name: str) -> list[dict]:
    """Return list of uploaded bundles via a temporary edit."""
    edit = service.edits().insert(packageName=package_name, body={}).execute()
    edit_id = edit["id"]
    try:
        result = service.edits().bundles().list(packageName=package_name, editId=edit_id).execute()
        return result.get("bundles", [])
    finally:
        service.edits().delete(packageName=package_name, editId=edit_id).execute()


def get_install_stats(
    service: Resource,
    package_name: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
) -> dict:
    """Fetch install/uninstall statistics from the Reporting API."""
    params = {
        "packageName": package_name,
        "startDate_year": int(start_date[:4]),
        "startDate_month": int(start_date[5:7]),
        "startDate_day": int(start_date[8:10]),
        "endDate_year": int(end_date[:4]),
        "endDate_month": int(end_date[5:7]),
        "endDate_day": int(end_date[8:10]),
        "dimensions": dimensions or ["date"],
        "metrics": metrics or ["activeDeviceInstalls"],
    }
    return service.stats().dimensions().get(**params).execute()
