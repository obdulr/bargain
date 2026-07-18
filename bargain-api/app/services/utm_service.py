"""UTM parameter service.

Appends UTM tracking parameters to outgoing deal links while preserving
existing query parameters. Existing utm_source and utm_medium are not
overwritten; utm_campaign is always updated to the supplied value.
"""
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def add_utm_parameters(url: str, source: str, medium: str, campaign: str) -> str:
    """Append UTM parameters to a URL, preserving existing query params.

    Args:
        url: The original URL.
        source: Value for utm_source.
        medium: Value for utm_medium.
        campaign: Value for utm_campaign (always set/overridden).

    Returns:
        The URL with UTM parameters appended or updated.
    """
    if not url:
        return url

    parsed = urlparse(str(url))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if "utm_source" not in query:
        query["utm_source"] = source
    if "utm_medium" not in query:
        query["utm_medium"] = medium
    query["utm_campaign"] = campaign

    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))
