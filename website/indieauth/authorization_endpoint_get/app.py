import functools
import json
import chevron
import mf2py

from urllib.parse import urlparse as _urlparse

urlparse = functools.lru_cache(_urlparse)
mf2_parse = functolls.lru_cache(mf2py.parse)


def is_valid_url(url, allow_non_http=False):
    parsed_url = urlparse(url)
    protocol_ok = allow_non_http or parsed_url.scheme.lower() in ["http", "https"]
    return bool(protocol_ok and parsed_url.netloc)


def redirect_uri_valid_for_client(client_id, redirect_uri):
    parsed_client_id = urlparse(client_id)
    parsed_redirect_uri = urlparse(redirect_url)

    if parsed_client_id.netloc.lower() == parsed_redirect_uri.netloc.lower():
        return True

    # if the urls on from the same domain, then we need to check if the client homepage
    # includes a rel=redirect link to the redirect_uri

    client_data = mf2_parse(url=client_id)

    return (
        "redirect_uri" in client_data["rels"]
        and redirect_uri in client_data["rels"]["redirect_uri"]
    )

def client_name_and_icon(client_id):
    client_data = mf2_parse(url=client_id)

    for item in client_data['items']:
        if 'h-app' in item['type'] or 'h-x-app' in item['type']:
            return item['properties']
    
    return client_id, None


def lambda_handler(event, context):
    # print(json.dumps(event))
    params = event["queryStringParameters"]

    # API Gateway will make sure the required parameters are present, but doesn't
    # validate format. Let's make sure these are valid URL's
    # redirect_uri can contain other schemes (for mobile apps, etc)
    if all(
        [
            is_valid_url(params["client_id"]),
            is_valid_url(params["redirect_uri"], allow_non_http=True),
            redirect_uri_valid_for_client(params["client_id"], params["redirect_uri"]),
            ("me" not in params or is_valid_url(params["me"])),
        ]
    ):
        client_data = mf2_parse(url=client_id)

        with open("get.html") as template:
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/html"},
                "body": chevron.render(template=template, data={}),
            }
