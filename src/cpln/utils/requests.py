import logging
import requests


def make_request(endpoint, token, request_method="GET", base_url = "", **kwargs):

    request_method = requests.get if "GET" else requests.post

    headers = {}
    url = f"{base_url}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = request_method(url, headers=headers, **kwargs)

    if response.status_code != 200:
        logging.error(
            f"API ERROR {response.status_code} - requested endpoint {endpoint}"
        )

        # delete cookie if the failed request was related to validation
        if response.status_code == 401:
            logging.debug("DELETE COOKIE AFTER API ERROR {response.status_code}")

        raise ValueError("API Error code, check logs for more info")

    try:
        return response.json()
    except:
        return response